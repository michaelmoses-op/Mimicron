from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ProblemError
from app.core.security import create_run_token
from app.db.models import Quota, Run, Scenario, ScenarioVersion
from app.messaging.kafka import publish_sim_command
from app.services.scenario_service import get_scenario, get_scenario_version


async def start_run(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    scenario_id: uuid.UUID,
    version: int | None,
    seed_override: int | None,
    mode_override: str | None,
    speed_override: float | None,
) -> tuple[Run, str]:
    scenario = await get_scenario(session, tenant_id, scenario_id)
    ver = version or scenario.current_version
    sv = await get_scenario_version(session, scenario.id, ver)
    quota = await session.get(Quota, tenant_id)
    if quota is None:
        raise ProblemError(status=402, title="Quota not configured")

    active = await session.scalar(
        select(func.count())
        .select_from(Run)
        .where(
            Run.tenant_id == tenant_id,
            Run.status.in_(["pending", "running", "paused"]),
        )
    )
    if active and active >= quota.max_concurrent_runs:
        raise ProblemError(status=409, title="Concurrent run limit reached")

    spec = sv.spec["spec"]
    seed = seed_override if seed_override is not None else int(spec.get("seed", 1))
    mode = mode_override or spec.get("time", {}).get("mode", "realtime")
    speed = speed_override or float(spec.get("time", {}).get("speed", 1))

    device_count = sum(int(f.get("count", 0)) for f in spec.get("fleets", []))

    run = Run(
        tenant_id=tenant_id,
        scenario_version_id=sv.id,
        status="pending",
        seed=seed,
        mode=mode,
        speed=speed,
        device_count=device_count,
    )
    session.add(run)
    await session.flush()

    run_token = create_run_token(tenant_id=tenant_id, run_id=run.id)
    await publish_sim_command(
        {
            "action": "start",
            "run_id": str(run.id),
            "tenant_id": str(tenant_id),
            "run_token": run_token,
            "scenario": sv.spec,
            "seed": seed,
            "mode": mode,
            "speed": speed,
            "ingestion_url": settings.ingestion_gateway_url,
        }
    )
    await session.commit()
    await session.refresh(run)
    return run, run_token


async def control_run(
    session: AsyncSession, *, tenant_id: uuid.UUID, run_id: uuid.UUID, action: str
) -> Run:
    run = await session.scalar(
        select(Run).where(Run.id == run_id, Run.tenant_id == tenant_id)
    )
    if run is None:
        raise ProblemError(status=404, title="Run not found")
    await publish_sim_command(
        {"action": action, "run_id": str(run.id), "tenant_id": str(tenant_id)}
    )
    if action == "stop":
        run.status = "stopped"
        run.ended_at = datetime.now(UTC)
    elif action == "pause":
        run.status = "paused"
    elif action == "resume":
        run.status = "running"
    await session.commit()
    await session.refresh(run)
    return run
