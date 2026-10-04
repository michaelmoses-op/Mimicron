from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def query_telemetry(
    engine: AsyncEngine,
    *,
    tenant_id: uuid.UUID,
    metric: str,
    from_ts: datetime,
    to_ts: datetime,
    run_id: uuid.UUID | None,
    device_id: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    sql = """
        SELECT time, device_id, value
        FROM measurements
        WHERE tenant_id = :tenant_id AND metric = :metric
          AND time >= :from_ts AND time <= :to_ts
    """
    params: dict[str, Any] = {
        "tenant_id": tenant_id,
        "metric": metric,
        "from_ts": from_ts,
        "to_ts": to_ts,
        "limit": limit,
    }
    if run_id:
        sql += " AND run_id = :run_id"
        params["run_id"] = run_id
    if device_id:
        sql += " AND device_id = :device_id"
        params["device_id"] = device_id
    sql += " ORDER BY time DESC LIMIT :limit"
    async with engine.connect() as conn:
        rows = (await conn.execute(text(sql), params)).mappings().all()
    return [dict(r) for r in rows]
