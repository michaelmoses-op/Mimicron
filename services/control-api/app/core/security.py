from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SCOPE_VALUES = frozenset({"ingest", "read", "simulate", "admin"})


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def hash_api_key(full_key: str) -> str:
    return hashlib.sha256(full_key.encode()).hexdigest()


def generate_api_key_material() -> tuple[str, str, str]:
    prefix = secrets.token_hex(4)
    secret = secrets.token_urlsafe(24)
    full = f"mc_live_{prefix}_{secret}"
    return prefix, full, hash_api_key(full)


def create_access_token(*, user_id: uuid.UUID, tenant_id: uuid.UUID, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=settings.jwt_access_ttl_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token_value() -> str:
    return secrets.token_urlsafe(48)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def create_run_token(*, tenant_id: uuid.UUID, run_id: uuid.UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "tenant_id": str(tenant_id),
        "run_id": str(run_id),
        "scopes": ["ingest"],
        "type": "run",
        "iat": now,
        "exp": now + timedelta(seconds=settings.jwt_run_ttl_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_stream_token(*, tenant_id: uuid.UUID, user_id: uuid.UUID) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    expires = now + timedelta(seconds=settings.jwt_stream_ttl_seconds)
    payload = {
        "tenant_id": str(tenant_id),
        "sub": str(user_id),
        "scopes": ["read"],
        "type": "stream",
        "iat": now,
        "exp": expires,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, expires
