from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Header, Request
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ProblemError
from app.core.ratelimit import check_api_rate_limit
from app.core.redis_client import get_redis
from app.core.security import decode_access_token, hash_api_key
from app.db.models import ApiKey, Membership, Quota, User
from app.db.session import get_session

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass
class UserPrincipal:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: str
    email: str


@dataclass
class ApiKeyPrincipal:
    tenant_id: uuid.UUID
    key_id: uuid.UUID
    scopes: list[str]


Principal = UserPrincipal | ApiKeyPrincipal


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_user_principal(
    request: Request,
    session: SessionDep,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UserPrincipal:
    if creds is None or creds.scheme.lower() != "bearer":
        raise ProblemError(status=401, title="Missing bearer token")
    try:
        payload = decode_access_token(creds.credentials)
    except jwt.PyJWTError as e:
        raise ProblemError(status=401, title="Invalid token") from e
    if payload.get("type") != "access":
        raise ProblemError(status=401, title="Invalid token type")

    user_id = uuid.UUID(payload["sub"])
    tenant_id = uuid.UUID(payload["tenant_id"])
    role = str(payload.get("role", "member"))

    user = await session.get(User, user_id)
    if user is None:
        raise ProblemError(status=401, title="User not found")

    membership = await session.scalar(
        select(Membership).where(
            Membership.user_id == user_id, Membership.tenant_id == tenant_id
        )
    )
    if membership is None:
        raise ProblemError(status=401, title="Membership not found")

    principal = UserPrincipal(
        user_id=user_id, tenant_id=tenant_id, role=membership.role or role, email=user.email
    )
    await _enforce_rate_limit(request, tenant_id, session)
    return principal


UserDep = Annotated[UserPrincipal, Depends(get_user_principal)]


def tenant_id_of(principal: Principal) -> uuid.UUID:
    return principal.tenant_id


def principal_has_scope(principal: Principal, *scopes: str) -> bool:
    if isinstance(principal, UserPrincipal):
        return True
    if "admin" in principal.scopes:
        return True
    return any(s in principal.scopes for s in scopes)


class _RequireScopes:
    def __init__(self, *scopes: str) -> None:
        self.scopes = scopes

    async def __call__(
        self,
        request: Request,
        session: SessionDep,
        creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
        api_key: Annotated[str | None, Depends(api_key_header)],
    ) -> Principal:
        principal = await get_api_key_or_user(request, session, creds, api_key)
        if not principal_has_scope(principal, *self.scopes):
            raise ProblemError(
                status=403,
                title="Insufficient scope",
                detail=f"Requires one of: {', '.join(self.scopes)}",
            )
        return principal


ReadDep = Annotated[Principal, Depends(_RequireScopes("read"))]
SimulateDep = Annotated[Principal, Depends(_RequireScopes("simulate"))]
AdminDep = Annotated[Principal, Depends(_RequireScopes("admin"))]


async def get_api_key_or_user(
    request: Request,
    session: SessionDep,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    api_key: Annotated[str | None, Depends(api_key_header)],
) -> Principal:
    if creds is not None and creds.scheme.lower() == "bearer":
        token = creds.credentials
        if token.startswith("mc_live_"):
            return await _principal_from_api_key(request, session, token)
        return await get_user_principal(request, session, creds)
    if api_key:
        return await _principal_from_api_key(request, session, api_key)
    raise ProblemError(status=401, title="Missing credentials")


async def _principal_from_api_key(
    request: Request, session: AsyncSession, full_key: str
) -> ApiKeyPrincipal:
    key_hash = hash_api_key(full_key)
    row = await session.scalar(select(ApiKey).where(ApiKey.key_hash == key_hash))
    if row is None or row.revoked_at is not None:
        raise ProblemError(status=401, title="Invalid API key")
    principal = ApiKeyPrincipal(tenant_id=row.tenant_id, key_id=row.id, scopes=list(row.scopes))
    await _enforce_rate_limit(request, row.tenant_id, session)
    return principal


async def _enforce_rate_limit(
    request: Request, tenant_id: uuid.UUID, session: AsyncSession
) -> None:
    quota = await session.get(Quota, tenant_id)
    if quota is None:
        return
    redis = get_redis()
    allowed, remaining, retry_after = await check_api_rate_limit(
        redis, tenant_id, quota.max_api_rps
    )
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = quota.max_api_rps
    if not allowed:
        raise ProblemError(
            status=429,
            title="Too many requests",
            type_="https://mimicron.dev/problems/rate-limit",
            extra={"retry_after": retry_after},
        )


def verify_internal_secret(
    x_internal_secret: Annotated[str | None, Header(alias="X-Internal-Secret")] = None,
) -> None:
    if x_internal_secret != settings.internal_api_secret:
        raise ProblemError(status=401, title="Invalid internal secret")
