from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import ReadDep, SessionDep, SimulateDep, tenant_id_of
from app.db.models import Run
from app.schemas.runs import RunCreate, RunOut, RunPage
from app.services import run_service

router = APIRouter(prefix="/v1/runs", tags=["runs"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=RunOut)
async def start_run(body: RunCreate, principal: SimulateDep, session: SessionDep) -> RunOut:
    run, _token = await run_service.start_run(
        session,
        tenant_id=tenant_id_of(principal),
        scenario_id=body.scenario_id,
        version=body.version,
        seed_override=body.seed_override,
        mode_override=body.mode_override,
        speed_override=body.speed_override,
    )
    return _to_out(await _load_run(session, tenant_id_of(principal), run.id))


@router.get("/{run_id}", response_model=RunOut)
async def get_run(run_id: uuid.UUID, principal: ReadDep, session: SessionDep) -> RunOut:
    return _to_out(await _load_run(session, tenant_id_of(principal), run_id))


@router.get("", response_model=RunPage)
async def list_runs(
    principal: ReadDep,
    session: SessionDep,
    limit: int = Query(50, ge=1, le=500),
    status_filter: str | None = Query(None, alias="status"),
) -> RunPage:
    tid = tenant_id_of(principal)
    q = (
        select(Run)
        .where(Run.tenant_id == tid)
        .options(selectinload(Run.scenario_version))
        .order_by(Run.created_at.desc())
        .limit(limit)
    )
    if status_filter:
        q = q.where(Run.status == status_filter)
    rows = list(await session.scalars(q))
    return RunPage(items=[_to_out(r) for r in rows], next_cursor=None)


@router.post("/{run_id}/{action}", status_code=status.HTTP_202_ACCEPTED, response_model=RunOut)
async def control_run(
    run_id: uuid.UUID, action: str, principal: SimulateDep, session: SessionDep
) -> RunOut:
    if action not in {"stop", "pause", "resume"}:
        from app.core.errors import ProblemError

        raise ProblemError(status=422, title="Invalid action")
    tid = tenant_id_of(principal)
    run = await run_service.control_run(
        session, tenant_id=tid, run_id=run_id, action=action
    )
    return _to_out(await _load_run(session, tenant_id_of(principal), run.id))


async def _load_run(session: AsyncSession, tenant_id: uuid.UUID, run_id: uuid.UUID) -> Run:
    from app.core.errors import ProblemError

    run = await session.scalar(
        select(Run)
        .where(Run.id == run_id, Run.tenant_id == tenant_id)
        .options(selectinload(Run.scenario_version))
    )
    if run is None:
        raise ProblemError(status=404, title="Run not found")
    return run


def _to_out(run: Run) -> RunOut:
    sv = run.scenario_version
    return RunOut(
        id=run.id,
        scenario_id=sv.scenario_id if sv else None,
        scenario_version=sv.version if sv else None,
        status=run.status,
        seed=int(run.seed) if run.seed is not None else None,
        mode=run.mode,
        device_count=run.device_count,
        events_emitted=int(run.events_emitted or 0),
        started_at=run.started_at,
        ended_at=run.ended_at,
        error=run.error,
    )
