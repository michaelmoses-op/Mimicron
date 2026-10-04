from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ScenarioWrite(BaseModel):
    scenario: dict = Field(description="Scenario document")
    spec_yaml: str | None = None


class ScenarioSummary(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    current_version: int
    updated_at: datetime


class ScenarioOut(ScenarioSummary):
    spec: dict
    spec_yaml: str | None = None
    checksum: str | None = None


class ScenarioPage(BaseModel):
    items: list[ScenarioSummary]
    next_cursor: str | None = None


class ValidationResult(BaseModel):
    valid: bool
    errors: list[dict[str, str]] = []
    estimate: dict | None = None
