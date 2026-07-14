"""Асинхронный движок SQLAlchemy и сессия на запрос."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.log_sql,
    # 10 соединений на воркер. Postgres у нас один на все сервисы,
    # поэтому верхнюю границу держим жёсткой и без overflow.
    pool_size=10,
    max_overflow=0,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


class Base(DeclarativeBase):
    """Базовый класс моделей."""


async def get_session() -> AsyncIterator[AsyncSession]:
    """Одна сессия на HTTP-запрос.

    Так все чтения внутри запроса видят согласованный снимок данных,
    а результат генерации пишется той же сессией, что собирала факты.
    """
    async with AsyncSessionLocal() as session:
        yield session
