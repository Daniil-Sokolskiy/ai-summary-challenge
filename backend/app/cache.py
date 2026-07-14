"""Redis: JSON-кэш и счётчики.

Клиент один на процесс, создаётся в lifespan приложения.
"""

import json
import logging
from typing import Any

from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)

JsonDict = dict[str, Any]

_redis: Redis | None = None


async def init_redis() -> None:
    global _redis
    _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await _redis.ping()


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis() -> Redis:
    if _redis is None:
        raise RuntimeError("Redis не инициализирован: init_redis() вызывается в lifespan")
    return _redis


async def cache_get(key: str) -> JsonDict | None:
    raw = await get_redis().get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Формат значения поменялся между релизами — считаем это промахом.
        logger.warning("не удалось разобрать значение кэша", extra={"key": key})
        return None


async def cache_set(key: str, value: JsonDict, ttl_seconds: int) -> None:
    await get_redis().set(key, json.dumps(value, ensure_ascii=False), ex=ttl_seconds)


async def cache_delete_pattern(pattern: str) -> int:
    """Удаляет ключи по маске. SCAN, а не KEYS — база общая с другими сервисами."""
    redis = get_redis()
    removed = 0
    async for key in redis.scan_iter(match=pattern, count=200):
        removed += await redis.delete(key)
    return removed


async def cache_incr(key: str, ttl_seconds: int) -> int:
    """Инкремент счётчика с TTL на первую запись."""
    redis = get_redis()
    value = await redis.incr(key)
    if value == 1:
        await redis.expire(key, ttl_seconds)
    return value


def ai_description_key(inn: str, facts_hash: str) -> str:
    return f"company:{inn}:ai-description:v1:{facts_hash}"


def ai_description_pattern(inn: str) -> str:
    return f"company:{inn}:ai-description:*"


def ai_feedback_key(inn: str, vote: str) -> str:
    return f"company:{inn}:ai-feedback:{vote}"
