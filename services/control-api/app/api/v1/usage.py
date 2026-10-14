from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.deps import ReadDep, SessionDep, tenant_id_of
from app.db.models import Quota, UsageDaily

router = APIRouter(prefix="/v1", tags=["usage"])


@router.get("/usage")
async def get_usage(
    principal: ReadDep,
    session: SessionDep,
    from_day: date | None = Query(None, alias="from"),
    to_day: date | None = Query(None, alias="to"),
) -> dict:
    tenant_id = tenant_id_of(principal)
    q = select(UsageDaily).where(UsageDaily.tenant_id == tenant_id).order_by(UsageDaily.day.desc())
    if from_day:
        q = q.where(UsageDaily.day >= from_day)
    if to_day:
        q = q.where(UsageDaily.day <= to_day)
    q = q.limit(90)
    rows = list(await session.scalars(q))
    quota = await session.get(Quota, tenant_id)
    return {
        "quota": {
            "max_devices": quota.max_devices if quota else 0,
            "max_events_per_sec": quota.max_events_per_sec if quota else 0,
            "max_concurrent_runs": quota.max_concurrent_runs if quota else 0,
            "max_run_duration_s": quota.max_run_duration_s if quota else 0,
            "retention_days": quota.retention_days if quota else 0,
            "max_api_rps": quota.max_api_rps if quota else 0,
        },
        "daily": [
            {
                "day": r.day.isoformat(),
                "events_ingested": int(r.events_ingested or 0),
                "events_rejected": int(r.events_rejected or 0),
                "api_calls": int(r.api_calls or 0),
                "sim_seconds": int(r.sim_seconds or 0),
            }
            for r in rows
        ],
    }
