from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query

from app.core.deps import ReadDep, tenant_id_of
from app.timescale.pool import get_timescale_engine
from app.timescale.queries import query_anomalies

router = APIRouter(prefix="/v1", tags=["telemetry"])


@router.get("/anomalies")
async def list_anomalies(
    principal: ReadDep,
    run_id: uuid.UUID | None = None,
    device_id: str | None = None,
    severity: str | None = None,
    from_ts: datetime | None = Query(None, alias="from"),
    to_ts: datetime | None = Query(None, alias="to"),
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    rows = await query_anomalies(
        get_timescale_engine(),
        tenant_id=tenant_id_of(principal),
        from_ts=from_ts,
        to_ts=to_ts,
        run_id=run_id,
        device_id=device_id,
        severity=severity,
        limit=limit,
    )
    items = [
        {
            "time": r["time"].isoformat(),
            "run_id": str(r["run_id"]) if r["run_id"] else None,
            "device_id": r["device_id"],
            "metric": r["metric"],
            "detector": r["detector"],
            "severity": r["severity"],
            "score": float(r["score"] or 0),
            "value": float(r["value"] or 0),
            "expected": float(r["expected"]) if r["expected"] is not None else None,
        }
        for r in rows
    ]
    return {"items": items, "next_cursor": None}
