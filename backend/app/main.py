"""Картотека — API карточки компании."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import debug, router
from app.cache import close_redis, init_redis
from app.config import settings
from app.db import AsyncSessionLocal, Base, engine
from app.debug import SqlCounterMiddleware, register_sql_counter
from app.seed import seed_if_empty

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

DB_CONNECT_ATTEMPTS = 15
DB_CONNECT_DELAY_SECONDS = 2.0


async def _wait_for_db() -> None:
    """Postgres поднимается чуть дольше, чем контейнер API."""
    for attempt in range(1, DB_CONNECT_ATTEMPTS + 1):
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return
        except (OSError, SQLAlchemyError) as error:
            logger.info("база ещё не готова (%s/%s): %s", attempt, DB_CONNECT_ATTEMPTS, error)
            await asyncio.sleep(DB_CONNECT_DELAY_SECONDS)
    raise RuntimeError("Postgres недоступен")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await _wait_for_db()

    # Alembic здесь избыточен: схема одна, база поднимается из docker compose up.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_if_empty(session)

    await init_redis()

    # Счётчик вешаем после сида, чтобы стартовые запросы не попали в статистику.
    register_sql_counter(engine)
    logger.info("сервис готов, LLM: %s (%s)", settings.llm_base_url, settings.llm_model)

    yield

    await close_redis()
    await engine.dispose()


app = FastAPI(title="Картотека API", version="1.0.0", lifespan=lifespan)

app.add_middleware(SqlCounterMiddleware)

# Фронт ходит в API через прокси Next.js, но в разработке удобно дёргать
# эндпоинты из браузера напрямую.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router.router)
app.include_router(debug.router)


@app.get("/health", tags=["service"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
