from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings

_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def api_key_cache_key(key_hash: str) -> str:
    return f"apikey:{key_hash}"


async def cache_api_key_verification(key_hash: str, payload: dict[str, Any]) -> None:
    redis = get_redis()
    await redis.setex(
        api_key_cache_key(key_hash),
        settings.api_key_cache_ttl_seconds,
        json.dumps(payload),
    )


async def evict_api_key_cache(key_hash: str) -> None:
    redis = get_redis()
    await redis.delete(api_key_cache_key(key_hash))
