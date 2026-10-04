from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class RunCreate(BaseModel):
    scenario_id: uuid.UUID
    version: int | None = None
    seed_override: int | None = None
    mode_override: str | None = None
    speed_override: float | None = None


class RunOut(BaseModel):
    id: uuid.UUID
    scenario_id: uuid.UUID | None = None
    scenario_version: int | None = None
    status: str
    seed: int | None = None
    mode: str | None = None
    device_count: int | None = None
    events_emitted: int = 0
    started_at: datetime | None = None
    ended_at: datetime | None = None
    error: str | None = None


class RunPage(BaseModel):
    items: list[RunOut]
    next_cursor: str | None = None
