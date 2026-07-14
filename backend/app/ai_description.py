"""Генерация ИИ-описания компании.

Схема: генератор пишет черновик по фактам карточки, критик его оценивает.
Если оценка низкая — переписываем черновик с учётом замечаний критика.
Если модель недоступна, отдаём текст, собранный из тех же фактов шаблоном.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date

from openai import AsyncOpenAI, OpenAIError, RateLimitError
from openai.types.chat import ChatCompletionMessageParam

from app.config import settings
from app.schemas import CompanyFacts

logger = logging.getLogger(__name__)

GENERATOR_MAX_TOKENS = 1500
CRITIC_MAX_TOKENS = 2000

GENERATOR_SYSTEM_PROMPT = """Ты — аналитик, который пишет краткое описание компании \
по данным из открытых реестров.

Требования к тексту:
* только факты из переданных данных, ничего не выдумывай;
* деловой тон, без рекламы и оценочных суждений;
* 4–7 предложений в каждом разделе;
* markdown с тремя разделами ровно в таком порядке и с такими заголовками:
## Финансовое состояние
## Надёжность
## Риски

Не добавляй заголовок первого уровня и не пиши вступление про то, что ты ИИ."""

CRITIC_SYSTEM_PROMPT = """Ты — строгий критик деловых текстов. Тебе дают факты о компании \
и черновик описания, написанный другой моделью.

Проверь черновик: нет ли выдуманных фактов, оценочных суждений, повторов; на месте ли \
разделы «Финансовое состояние», «Надёжность», «Риски».

Ответь строго JSON-объектом:
{"score": <целое 0-100>, "feedback": "<что исправить, одной-двумя фразами>", \
"final_text": <исправленный текст или null>}"""

_client = AsyncOpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    timeout=settings.llm_timeout_seconds,
)


@dataclass(slots=True)
class LlmReply:
    text: str
    model: str


@dataclass(slots=True)
class CriticVerdict:
    score: int
    feedback: str
    final_text: str | None


@dataclass(slots=True)
class GeneratedDescription:
    text: str
    score: int
    is_llm: bool
    model: str | None = None
    history: list[str] = field(default_factory=list)


def _money(value: float | int | None) -> str:
    if not value:
        return "нет данных"
    return f"{int(value):,} ₽".replace(",", " ")


def _human_date(value: date | None) -> str:
    return value.strftime("%d.%m.%Y") if value else "нет данных"


def build_generator_user_prompt(facts: CompanyFacts, feedback: str | None) -> str:
    counts = facts.section_counts
    lines = [
        f"Название: {facts.name}",
        f"ИНН: {facts.inn}",
        f"Полное наименование: {facts.full_name}",
        f"Статус: {facts.status}",
        f"Дата регистрации: {_human_date(facts.registration_date)}",
        f"Город: {facts.city} ({facts.region})",
        f"Руководитель: {facts.ceo_name or 'нет данных'}",
        f"Уставный капитал: {_money(facts.charter_capital)}",
        f"Основной ОКВЭД: {facts.main_okved_code} — {facts.main_okved_name}",
        "",
        f"Выручка за {facts.revenue_year or 'последний год'}: {_money(facts.revenue)}",
        f"Прибыль: {_money(facts.profit)}",
        f"Численность сотрудников: {facts.headcount if facts.headcount else 'нет данных'}",
        "",
        f"Судебных дел: {counts.court_cases}, на сумму {_money(facts.court_amount_total)}",
        f"Основные категории споров: {', '.join(facts.court_top_categories) or 'нет'}",
        f"Исполнительных производств: {counts.enforcement}, "
        f"на сумму {_money(facts.enforcement_amount_total)}",
        f"Госконтрактов: {counts.contracts}, на сумму {_money(facts.contracts_amount_total)}",
        f"Лицензий: {counts.licenses}, из них действующих: {facts.active_licenses}",
        f"Проверок: {counts.inspections}, выявлено нарушений: {facts.inspection_violations}",
        f"Связанных организаций: {counts.relations}",
        f"Ключевые связи: {', '.join(facts.key_relations) or 'нет'}",
        f"Изменений в реестре: {counts.changes}, последнее — {_human_date(facts.last_change_at)}",
    ]
    if feedback:
        lines += [
            "",
            "Предыдущий черновик забракован. Замечания редактора, которые нужно учесть:",
            feedback,
        ]
    return "\n".join(lines)


def build_critic_user_prompt(facts: CompanyFacts, draft: str) -> str:
    return (
        f"Факты о компании:\n{build_generator_user_prompt(facts, None)}\n\n"
        f"Черновик описания:\n{draft}"
    )


def _generator_messages(
    facts: CompanyFacts, feedback: str | None
) -> list[ChatCompletionMessageParam]:
    return [
        {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
        {"role": "user", "content": build_generator_user_prompt(facts, feedback)},
    ]


def _critic_messages(facts: CompanyFacts, draft: str) -> list[ChatCompletionMessageParam]:
    return [
        {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
        {"role": "user", "content": build_critic_user_prompt(facts, draft)},
    ]


async def _create_with_fallback(
    messages: list[ChatCompletionMessageParam],
    *,
    max_tokens: int,
    temperature: float,
    json_response: bool = False,
) -> LlmReply:
    """Вызов модели с подстраховкой платной моделью.

    Лимит бесплатной модели общий на аккаунт, поэтому 429 прилетает и тогда,
    когда лично мы ничего плохого не делаем. В этом случае повторяем вызов
    на платной модели — она дороже, но лимит у неё отдельный.
    """
    extra: dict[str, object] = {}
    if json_response:
        extra["response_format"] = {"type": "json_object"}

    try:
        completion = await _client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **extra,
        )
        model_used = settings.llm_model
    except RateLimitError:
        logger.warning("лимит бесплатной модели исчерпан, уходим на %s", settings.llm_model_fallback)
        completion = await _client.chat.completions.create(
            model=settings.llm_model_fallback,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **extra,
        )
        model_used = settings.llm_model_fallback

    content = completion.choices[0].message.content or ""
    return LlmReply(text=content.strip(), model=model_used)


def _parse_review(raw: str) -> CriticVerdict:
    """Критик иногда оборачивает JSON в markdown-блок — снимаем обёртку."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("критик ответил не JSON-ом, черновик остаётся как есть")
        return CriticVerdict(score=0, feedback="", final_text=None)

    score = payload.get("score")
    final_text = payload.get("final_text")
    return CriticVerdict(
        score=int(score) if isinstance(score, (int, float)) else 0,
        feedback=str(payload.get("feedback") or ""),
        final_text=final_text if isinstance(final_text, str) and final_text.strip() else None,
    )


def _looks_like_description(text: str) -> bool:
    """Минимальная проверка, что модель вернула описание, а не отписку."""
    return len(text) >= 200 and "## " in text


async def generate_description_with_review(facts: CompanyFacts) -> GeneratedDescription:
    """Генерация с проверкой критиком.

    Первый черновик почти всегда проходит, второй заход нужен для тех карточек,
    где данных мало и модель начинает фантазировать.
    """
    history: list[str] = []
    feedback: str | None = None
    best: LlmReply | None = None
    best_score = 0

    try:
        for attempt in range(1, settings.ai_max_attempts + 1):
            draft = await _create_with_fallback(
                _generator_messages(facts, feedback),
                max_tokens=GENERATOR_MAX_TOKENS,
                temperature=0.4,
            )
            if not _looks_like_description(draft.text):
                logger.warning(
                    "модель вернула непригодный текст, попытка %s, инн %s", attempt, facts.inn
                )
                break

            history.append(draft.text)

            review = await _create_with_fallback(
                _critic_messages(facts, draft.text),
                max_tokens=CRITIC_MAX_TOKENS,
                temperature=0.0,
                json_response=True,
            )
            verdict = _parse_review(review.text)
            text = verdict.final_text or draft.text
            best = LlmReply(text=text, model=draft.model)
            best_score = verdict.score

            if verdict.score >= settings.ai_min_score:
                return GeneratedDescription(
                    text=text,
                    score=verdict.score,
                    is_llm=True,
                    model=draft.model,
                    history=history,
                )

            logger.info(
                "критик поставил %s, переписываем описание: %s", verdict.score, verdict.feedback
            )
            feedback = verdict.feedback
    except OpenAIError as error:
        logger.warning("провайдер не ответил (инн %s): %s", facts.inn, error)

    if best is not None:
        # Попытки кончились, но текст у нас есть — показываем лучшее, что получилось.
        return GeneratedDescription(
            text=best.text,
            score=best_score,
            is_llm=True,
            model=best.model,
            history=history,
        )

    return build_template_description(facts)


def build_template_description(facts: CompanyFacts) -> GeneratedDescription:
    """Описание из фактов без участия модели.

    Формат тот же, что у модели, — карточка не должна оставаться пустой,
    если провайдер лежит.
    """
    counts = facts.section_counts
    registration = _human_date(facts.registration_date)
    financial_lines = [
        f"Выручка за {facts.revenue_year or 'последний отчётный год'} — {_money(facts.revenue)}, "
        f"прибыль — {_money(facts.profit)}.",
        f"Заявленная численность сотрудников: "
        f"{facts.headcount if facts.headcount else 'нет данных'}.",
        f"Госконтрактов: {counts.contracts} на сумму {_money(facts.contracts_amount_total)}.",
    ]
    reliability_lines = [
        f"{facts.full_name} зарегистрирована {registration} в городе {facts.city}, "
        f"текущий статус — «{facts.status.lower()}».",
        f"Основной вид деятельности: {facts.main_okved_code} — {facts.main_okved_name}.",
        f"Действующих лицензий: {facts.active_licenses}. "
        f"Связанных организаций: {counts.relations}.",
    ]
    risk_lines = [
        f"Судебных дел: {counts.court_cases} на сумму {_money(facts.court_amount_total)}.",
        f"Исполнительных производств: {counts.enforcement} "
        f"на сумму {_money(facts.enforcement_amount_total)}.",
        f"Проверок: {counts.inspections}, выявлено нарушений: {facts.inspection_violations}.",
    ]

    text = "\n".join(
        [
            f"{facts.name} (ИНН {facts.inn}) — сведения из открытых реестров.",
            "",
            "## Финансовое состояние",
            *financial_lines,
            "",
            "## Надёжность",
            *reliability_lines,
            "",
            "## Риски",
            *risk_lines,
        ]
    )
    return GeneratedDescription(text=text, score=0, is_llm=False, model=None, history=[])
