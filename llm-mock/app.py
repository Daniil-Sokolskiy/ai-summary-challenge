"""OpenAI-совместимый мок LLM-провайдера.

Ведёт себя как реальный провайдер на free-tier:
  * генерация занимает секунды, а не миллисекунды;
  * лимит запросов в минуту общий на весь аккаунт (не на ключ, не на IP);
  * при превышении отдаёт 429 с заголовками X-RateLimit-*.

Дополнительно считает статистику — /admin/stats. Это единственный честный
способ узнать, сколько платных вызовов на самом деле сделало приложение.
"""

import asyncio
import hashlib
import json
import os
import random
import re
import time
from collections import Counter, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

LATENCY_MIN = float(os.getenv("LLM_LATENCY_MIN", "7.0"))
LATENCY_MAX = float(os.getenv("LLM_LATENCY_MAX", "9.0"))
RATE_LIMIT_PER_MIN = int(os.getenv("LLM_RATE_LIMIT_PER_MIN", "16"))

app = FastAPI(title="llm-mock")


class MockState:
    """Настройки и счётчики. Меняются через /admin/*, живут в памяти процесса."""

    def __init__(self) -> None:
        self.latency_min = LATENCY_MIN
        self.latency_max = LATENCY_MAX
        self.rate_limit_per_min = RATE_LIMIT_PER_MIN
        self.fail_mode = False  # 500 на каждый вызов — имитация лежащего провайдера
        self.reset_counters()

    def reset_counters(self) -> None:
        self.calls_ok = 0
        self.calls_429 = 0
        self.calls_500 = 0
        self.seconds_spent = 0.0
        self.calls_by_model: Counter[str] = Counter()
        self.calls_by_kind: Counter[str] = Counter()
        self.generations_by_inn: Counter[str] = Counter()
        self.window: deque[float] = deque()


state = MockState()
_lock = asyncio.Lock()


async def _take_rate_limit_slot() -> bool:
    """Скользящее окно в 60 секунд, общее на весь аккаунт."""
    async with _lock:
        now = time.monotonic()
        while state.window and now - state.window[0] >= 60.0:
            state.window.popleft()
        if len(state.window) >= state.rate_limit_per_min:
            return False
        state.window.append(now)
        return True


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    max_tokens: int | None = None
    temperature: float | None = None
    response_format: dict | None = None


def _classify(request: ChatRequest) -> str:
    """Генерация или проверка текста критиком — по системному промпту."""
    system = next((m.content for m in request.messages if m.role == "system"), "")
    if "критик" in system.lower() or "critic" in system.lower():
        return "critic"
    return "generate"


def _extract_inn(request: ChatRequest) -> str:
    user = next((m.content for m in request.messages if m.role == "user"), "")
    match = re.search(r"\b(\d{10}|\d{12})\b", user)
    return match.group(1) if match else "unknown"


def _extract_company_name(request: ChatRequest) -> str:
    user = next((m.content for m in request.messages if m.role == "user"), "")
    match = re.search(r"Название:\s*(.+)", user)
    return match.group(1).strip() if match else "Компания"


def _description_text(name: str, inn: str) -> str:
    """Детерминированный по ИНН текст в том же формате, что отдаёт реальная модель."""
    seed = int(hashlib.sha1(inn.encode()).hexdigest()[:8], 16)
    rnd = random.Random(seed)
    tone = rnd.choice(["устойчивое", "стабильное", "неоднозначное"])
    return f"""{name} (ИНН {inn}) — действующая организация, зарегистрированная в ЕГРЮЛ.
По совокупности открытых данных положение компании выглядит {tone}.

## Финансовое состояние
Выручка последнего отчётного года сопоставима с предыдущим периодом.
Значимых кассовых разрывов по доступным данным не выявлено.

## Надёжность
Компания не находится в процессе ликвидации, признаков недостоверности сведений
в реестре не зафиксировано. Массовых адресов регистрации не обнаружено.

## Риски
Судебная нагрузка находится в пределах, обычных для отрасли и масштаба выручки.
Исполнительных производств, критичных для операционной деятельности, нет.
"""


def _critic_text() -> str:
    """Критик отвечает JSON-ом: оценка, замечания и, возможно, переписанный текст.

    Оценка стабильно ниже порога, за которым текст принимают с первой попытки, —
    так же ведёт себя и живая модель-критик на наших промптах.
    """
    return json.dumps(
        {
            "score": random.choice([68, 72, 76, 80]),
            "feedback": "Уточнить формулировки в разделе «Риски», убрать оценочные суждения.",
            "final_text": None,
        },
        ensure_ascii=False,
    )


def _completion_body(model: str, content: str) -> dict:
    return {
        "id": f"chatcmpl-{random.randint(10**9, 10**10)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 900, "completion_tokens": 420, "total_tokens": 1320},
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest) -> JSONResponse:
    kind = _classify(request)
    inn = _extract_inn(request)

    if not await _take_rate_limit_slot():
        state.calls_429 += 1
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "message": "Rate limit exceeded: free-models-per-min",
                    "type": "rate_limit_error",
                    "code": 429,
                }
            },
            headers={
                "X-RateLimit-Limit": str(state.rate_limit_per_min),
                "X-RateLimit-Remaining": "0",
                "Retry-After": "60",
            },
        )

    delay = random.uniform(state.latency_min, state.latency_max)
    await asyncio.sleep(delay)
    state.seconds_spent += delay

    if state.fail_mode:
        state.calls_500 += 1
        return JSONResponse(
            status_code=500,
            content={"error": {"message": "upstream model unavailable", "code": 500}},
        )

    state.calls_ok += 1
    state.calls_by_model[request.model] += 1
    state.calls_by_kind[kind] += 1
    if kind == "generate":
        state.generations_by_inn[inn] += 1

    if kind == "critic":
        content = _critic_text()
    else:
        content = _description_text(_extract_company_name(request), inn)

    return JSONResponse(status_code=200, content=_completion_body(request.model, content))


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/admin/stats")
async def stats() -> dict:
    """Сколько на самом деле стоило приложение. Основной измерительный прибор."""
    total = state.calls_ok + state.calls_429 + state.calls_500
    return {
        "calls_total": total,
        "calls_ok": state.calls_ok,
        "calls_429": state.calls_429,
        "calls_500": state.calls_500,
        "llm_seconds_spent": round(state.seconds_spent, 1),
        "by_model": dict(state.calls_by_model),
        "by_kind": dict(state.calls_by_kind),
        "generations_by_inn": dict(state.generations_by_inn),
        "config": {
            "latency_min": state.latency_min,
            "latency_max": state.latency_max,
            "rate_limit_per_min": state.rate_limit_per_min,
            "fail_mode": state.fail_mode,
        },
    }


@app.post("/admin/reset")
async def reset() -> dict:
    state.reset_counters()
    return {"status": "reset"}


class ConfigPatch(BaseModel):
    latency_min: float | None = None
    latency_max: float | None = None
    rate_limit_per_min: int | None = None
    fail_mode: bool | None = None


@app.post("/admin/config")
async def config(patch: ConfigPatch) -> dict:
    """Чтобы воспроизводить сценарии: быстрая модель, лежащий провайдер, жёсткий лимит."""
    if patch.latency_min is not None:
        state.latency_min = patch.latency_min
    if patch.latency_max is not None:
        state.latency_max = patch.latency_max
    if patch.rate_limit_per_min is not None:
        state.rate_limit_per_min = patch.rate_limit_per_min
    if patch.fail_mode is not None:
        state.fail_mode = patch.fail_mode
    return await stats()


@app.middleware("http")
async def log_calls(request: Request, call_next):
    response = await call_next(request)
    return response
