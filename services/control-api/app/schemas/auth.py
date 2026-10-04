from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import QuotaOut


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10)
    tenant_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class MeOut(BaseModel):
    user_id: uuid.UUID
    email: str
    tenant_id: uuid.UUID
    tenant_name: str
    role: str
    quota: QuotaOut
