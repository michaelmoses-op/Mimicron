from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query

from app.core.deps import UserDep
from app.timescale.pool import get_timescale_engine
from app.timescale.queries import query_traffic_rollups

router = APIRouter(prefix="/v1", tags=["telemetry"])


@router.get("/traffic")
async def get_traffic_rollups(
    principal: UserDep,
    from_ts: datetime = Query(..., alias="from"),
    to_ts: datetime = Query(..., alias="to"),
    run_id: uuid.UUID | None = None,
    flow: str | None = None,
    region: str | None = None,
    limit: int = Query(500, ge=1, le=2000),
) -> dict:
    rows = await query_traffic_rollups(
        get_timescale_engine(),
        tenant_id=principal.tenant_id,
        from_ts=from_ts,
        to_ts=to_ts,
        run_id=run_id,
        flow=flow,
        region=region,
        limit=limit,
    )
    items = []
    for r in rows:
        req = int(r["requests"] or 0)
        err = int(r["errors"] or 0)
        items.append(
            {
                "time": r["time"].isoformat(),
                "run_id": str(r["run_id"]) if r["run_id"] else None,
                "flow": r["flow"],
                "region": r["region"],
                "requests": req,
                "errors": err,
                "error_rate": (err / req) if req else 0.0,
                "rps": req / 10.0,
                "p50_ms": float(r["p50_ms"] or 0),
                "p95_ms": float(r["p95_ms"] or 0),
                "p99_ms": float(r["p99_ms"] or 0),
                "bytes": int(r["bytes"] or 0),
            }
        )
    return {"interval": "10s", "items": items, "next_cursor": None}
