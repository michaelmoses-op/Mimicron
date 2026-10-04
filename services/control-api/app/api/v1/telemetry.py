from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query

from app.core.deps import UserDep
from app.timescale.pool import get_timescale_engine
from app.timescale.queries import query_telemetry

router = APIRouter(prefix="/v1", tags=["telemetry"])


@router.get("/telemetry")
async def get_telemetry(
    principal: UserDep,
    metric: str = Query(...),
    from_ts: datetime = Query(..., alias="from"),
    to_ts: datetime = Query(..., alias="to"),
    run_id: uuid.UUID | None = None,
    device_id: str | None = None,
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    rows = await query_telemetry(
        get_timescale_engine(),
        tenant_id=principal.tenant_id,
        metric=metric,
        from_ts=from_ts,
        to_ts=to_ts,
        run_id=run_id,
        device_id=device_id,
        limit=limit,
    )
    return {
        "metric": metric,
        "interval": "raw",
        "items": [
            {"time": r["time"].isoformat(), "device_id": r["device_id"], "value": r["value"]}
            for r in rows
        ],
        "next_cursor": None,
    }
