from __future__ import annotations

import time
import uuid

from redis.asyncio import Redis


async def check_api_rate_limit(
    redis: Redis, tenant_id: uuid.UUID, limit: int
) -> tuple[bool, int, int]:
    """Fixed window per UTC second. Returns allowed, remaining, retry_after_seconds."""
    if limit <= 0:
        return True, limit, 0
    window = int(time.time())
    key = f"rl:api:{tenant_id}:{window}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 2)
    remaining = max(0, limit - count)
    allowed = count <= limit
    retry_after = 1 if not allowed else 0
    return allowed, remaining, retry_after
