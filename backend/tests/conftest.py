"""Тесты гоняются внутри контейнера api: docker compose exec api pytest

Им нужны живые Postgres, Redis и llm-mock — те же, что у приложения.
"""

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

DEMO_INN = "7707410283"


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        # Холодная генерация описания идёт десятки секунд — таймаут с запасом.
        async with AsyncClient(
            transport=transport, base_url="http://api", timeout=120.0
        ) as http_client:
            yield http_client
