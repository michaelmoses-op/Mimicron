from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.db.models import GroundTruthLabel, Run
from app.db.session import get_session_factory
from app.messaging.kafka import sim_events_consumer

logger = logging.getLogger("control-api.sim-events")


async def run_sim_events_worker(stop: asyncio.Event) -> None:
    consumer = sim_events_consumer()
    await consumer.start()
    try:
        while not stop.is_set():
            try:
                msg = await asyncio.wait_for(consumer.getone(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            try:
                payload = json.loads(msg.value.decode())
                await handle_sim_event(payload)
            except Exception:
                logger.exception("sim event handling failed")
    finally:
        await consumer.stop()


async def handle_sim_event(payload: dict) -> None:
    event_type = payload.get("type")
    run_id = uuid.UUID(payload["run_id"])
    factory = get_session_factory()
    async with factory() as session:
        run = await session.get(Run, run_id)
        if run is None:
            return
        if event_type == "run.started":
            run.status = "running"
            run.started_at = datetime.now(UTC)
        elif event_type == "run.progress":
            run.events_emitted = int(payload.get("events_emitted", run.events_emitted))
        elif event_type == "run.completed":
            run.status = "completed"
            run.ended_at = datetime.now(UTC)
            run.events_emitted = int(payload.get("events_emitted", run.events_emitted))
        elif event_type == "run.failed":
            run.status = "failed"
            run.ended_at = datetime.now(UTC)
            run.error = payload.get("error")
        elif event_type == "ground_truth":
            session.add(
                GroundTruthLabel(
                    tenant_id=run.tenant_id,
                    run_id=run.id,
                    device_id=payload.get("device_id"),
                    metric=payload.get("metric"),
                    kind=payload.get("kind"),
                    magnitude=payload.get("magnitude"),
                    start_time=_parse_ts(payload.get("start_time")),
                    end_time=_parse_ts(payload.get("end_time")),
                    source_event=payload.get("source_event"),
                )
            )
        await session.commit()


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))
