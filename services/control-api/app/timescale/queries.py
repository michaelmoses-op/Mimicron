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


async def query_traffic_rollups(
    engine: AsyncEngine,
    *,
    tenant_id: uuid.UUID,
    from_ts: datetime,
    to_ts: datetime,
    run_id: uuid.UUID | None,
    flow: str | None,
    region: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    sql = """
        SELECT time, run_id, flow, region, requests, errors, p50_ms, p95_ms, p99_ms, bytes
        FROM traffic_rollups_10s
        WHERE tenant_id = :tenant_id
          AND time >= :from_ts AND time <= :to_ts
    """
    params: dict[str, Any] = {
        "tenant_id": tenant_id,
        "from_ts": from_ts,
        "to_ts": to_ts,
        "limit": limit,
    }
    if run_id:
        sql += " AND run_id = :run_id"
        params["run_id"] = run_id
    if flow:
        sql += " AND flow = :flow"
        params["flow"] = flow
    if region:
        sql += " AND region = :region"
        params["region"] = region
    sql += " ORDER BY time ASC LIMIT :limit"
    async with engine.connect() as conn:
        rows = (await conn.execute(text(sql), params)).mappings().all()
    return [dict(r) for r in rows]


async def query_anomalies(
    engine: AsyncEngine,
    *,
    tenant_id: uuid.UUID,
    from_ts: datetime | None,
    to_ts: datetime | None,
    run_id: uuid.UUID | None,
    device_id: str | None,
    severity: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    sql = """
        SELECT time, run_id, device_id, metric, detector, severity, score, value, expected
        FROM anomalies
        WHERE tenant_id = :tenant_id
    """
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}
    if from_ts:
        sql += " AND time >= :from_ts"
        params["from_ts"] = from_ts
    if to_ts:
        sql += " AND time <= :to_ts"
        params["to_ts"] = to_ts
    if run_id:
        sql += " AND run_id = :run_id"
        params["run_id"] = run_id
    if device_id:
        sql += " AND device_id = :device_id"
        params["device_id"] = device_id
    if severity:
        sql += " AND severity = :severity"
        params["severity"] = severity
    sql += " ORDER BY time DESC LIMIT :limit"
    async with engine.connect() as conn:
        rows = (await conn.execute(text(sql), params)).mappings().all()
    return [dict(r) for r in rows]
