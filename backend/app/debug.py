"""Счётчик SQL-запросов и отладочные эндпоинты.

Считаем каждый запрос, ушедший в базу, и раскладываем по эндпоинтам.
Нужно, чтобы отвечать на вопрос «сколько запросов стоит один показ карточки»
не на глаз, а числом.
"""

import re
from collections import Counter
from contextvars import ContextVar
from typing import Any

from fastapi import APIRouter
from sqlalchemy import delete, event
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.types import ASGIApp, Receive, Scope, Send

from app.cache import ai_description_pattern, cache_delete_pattern
from app.db import AsyncSessionLocal
from app.models import CompanyAiDescription
from app.schemas import DebugStats

UNKNOWN_ENDPOINT = "-"

current_endpoint: ContextVar[str] = ContextVar("current_endpoint", default=UNKNOWN_ENDPOINT)

_INN_SEGMENT = re.compile(r"^\d{10}(\d{2})?$")

_total = 0
_by_endpoint: Counter[str] = Counter()
_listener_installed = False


def endpoint_label(path: str) -> str:
    """/v1/company/7707410283/summary -> /v1/company/{inn}/summary"""
    segments = [
        "{inn}" if _INN_SEGMENT.match(segment) else segment for segment in path.split("/")
    ]
    return "/".join(segments) or "/"


def register_sql_counter(engine: AsyncEngine) -> None:
    """Вешает счётчик на курсор синхронного движка под асинхронным."""
    global _listener_installed
    if _listener_installed:
        return

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def _count_query(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        global _total
        _total += 1
        _by_endpoint[current_endpoint.get()] += 1

    _listener_installed = True


def reset_sql_counter() -> None:
    global _total
    _total = 0
    _by_endpoint.clear()


def sql_stats() -> DebugStats:
    return DebugStats(sql_queries_total=_total, sql_queries_by_endpoint=dict(_by_endpoint))


class SqlCounterMiddleware:
    """Проставляет текущий эндпоинт в контекст запроса.

    Пишем именно ASGI-мидлварь, а не @app.middleware: contextvar должен жить
    в той же задаче, в которой потом выполняются запросы к базе.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        token = current_endpoint.set(endpoint_label(scope["path"]))
        try:
            await self.app(scope, receive, send)
        finally:
            current_endpoint.reset(token)


router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/stats", response_model=DebugStats)
async def get_stats() -> DebugStats:
    return sql_stats()


@router.post("/reset")
async def reset_stats() -> dict[str, str]:
    reset_sql_counter()
    return {"status": "reset"}


@router.post("/purge/{inn}")
async def purge_description(inn: str) -> dict[str, int]:
    """Забыть сгенерированное описание компании — и в Redis, и в базе.

    Нужно, чтобы «холодное открытие» можно было воспроизвести больше одного раза:
    без этого второй прогон измерений упирается в кэш и ничего не показывает.
    """
    keys_removed = await cache_delete_pattern(ai_description_pattern(inn))
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            delete(CompanyAiDescription).where(CompanyAiDescription.inn == inn)
        )
        await session.commit()
    return {"cache_keys_removed": keys_removed, "rows_removed": result.rowcount or 0}
