from __future__ import annotations

from datetime import UTC, datetime, timedelta

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ProblemError
from app.core.quotas import quota_for_tier
from app.core.security import (
    create_access_token,
    create_refresh_token_value,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models import Membership, Quota, RefreshToken, Tenant, User


async def register_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    tenant_name: str | None,
) -> tuple[User, Tenant, Membership, str, str]:
    existing = await session.scalar(select(User).where(User.email == email))
    if existing:
        raise ProblemError(
            status=409,
            title="Email already registered",
            type_="https://mimicron.dev/problems/conflict",
        )

    user = User(email=email, password_hash=hash_password(password))
    session.add(user)
    await session.flush()

    name = tenant_name or f"{email.split('@')[0]}'s workspace"
    base_slug = slugify(name) or "tenant"
    slug = base_slug
    suffix = 0
    while await session.scalar(select(Tenant).where(Tenant.slug == slug)):
        suffix += 1
        slug = f"{base_slug}-{suffix}"

    tenant = Tenant(name=name, slug=slug, tier="free")
    session.add(tenant)
    await session.flush()

    membership = Membership(tenant_id=tenant.id, user_id=user.id, role="owner")
    session.add(membership)

    defaults = quota_for_tier(tenant.tier)
    session.add(
        Quota(
            tenant_id=tenant.id,
            max_devices=defaults.max_devices,
            max_events_per_sec=defaults.max_events_per_sec,
            max_concurrent_runs=defaults.max_concurrent_runs,
            max_run_duration_s=defaults.max_run_duration_s,
            retention_days=defaults.retention_days,
            max_api_rps=defaults.max_api_rps,
        )
    )

    refresh_value = create_refresh_token_value()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_value),
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.jwt_refresh_ttl_seconds),
        )
    )
    await session.commit()
    await session.refresh(user)
    await session.refresh(tenant)

    access = create_access_token(user_id=user.id, tenant_id=tenant.id, role=membership.role)
    return user, tenant, membership, access, refresh_value


async def login_user(
    session: AsyncSession, *, email: str, password: str
) -> tuple[User, Tenant, Membership, str, str]:
    user = await session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise ProblemError(
            status=401,
            title="Invalid credentials",
            type_="https://mimicron.dev/problems/unauthorized",
        )

    membership = await session.scalar(
        select(Membership).where(Membership.user_id == user.id).limit(1)
    )
    if membership is None:
        raise ProblemError(status=401, title="No tenant membership")

    tenant = await session.get(Tenant, membership.tenant_id)
    if tenant is None:
        raise ProblemError(status=401, title="Tenant not found")

    refresh_value = create_refresh_token_value()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_value),
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.jwt_refresh_ttl_seconds),
        )
    )
    await session.commit()

    access = create_access_token(user_id=user.id, tenant_id=tenant.id, role=membership.role)
    return user, tenant, membership, access, refresh_value


async def refresh_tokens(session: AsyncSession, *, refresh_token: str) -> tuple[str, str]:
    token_hash = hash_token(refresh_token)
    row = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    now = datetime.now(UTC)
    if row is None or row.revoked_at is not None or row.expires_at < now:
        raise ProblemError(
            status=401,
            title="Invalid refresh token",
            type_="https://mimicron.dev/problems/unauthorized",
        )

    row.revoked_at = now
    user = await session.get(User, row.user_id)
    if user is None:
        raise ProblemError(status=401, title="Invalid refresh token")

    membership = await session.scalar(
        select(Membership).where(Membership.user_id == user.id).limit(1)
    )
    if membership is None:
        raise ProblemError(status=401, title="No tenant membership")

    new_refresh = create_refresh_token_value()
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(new_refresh),
            expires_at=now + timedelta(seconds=settings.jwt_refresh_ttl_seconds),
        )
    )
    await session.commit()

    access = create_access_token(
        user_id=user.id, tenant_id=membership.tenant_id, role=membership.role
    )
    return access, new_refresh
