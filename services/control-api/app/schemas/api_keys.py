from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Scope = Literal["ingest", "read", "simulate", "admin"]


class ApiKeyCreate(BaseModel):
    name: str = Field(max_length=100)
    scopes: list[Scope] = Field(min_length=1)
    expires_at: datetime | None = None


class ApiKeyOut(BaseModel):
    id: uuid.UUID
    name: str
    prefix: str
    scopes: list[Scope]
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None


class ApiKeyCreated(ApiKeyOut):
    secret: str


class ApiKeyPage(BaseModel):
    items: list[ApiKeyOut]
    next_cursor: str | None
