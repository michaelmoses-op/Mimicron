from __future__ import annotations

import base64
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.core.quotas import quota_from_model
from app.core.redis_client import cache_api_key_verification, evict_api_key_cache
from app.core.security import SCOPE_VALUES, generate_api_key_material
from app.db.models import ApiKey, Quota


def encode_cursor(created_at: datetime, key_id: uuid.UUID) -> str:
    raw = f"{created_at.isoformat()}|{key_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        ts, kid = raw.split("|", 1)
        return datetime.fromisoformat(ts), uuid.UUID(kid)
    except (ValueError, UnicodeDecodeError) as e:
        raise ProblemError(status=422, title="Invalid cursor") from e


async def create_api_key(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    scopes: list[str],
    expires_at: datetime | None,
) -> tuple[ApiKey, str]:
    invalid = [s for s in scopes if s not in SCOPE_VALUES]
    if invalid:
        raise ProblemError(status=422, title="Invalid scopes", detail=f"Unknown scopes: {invalid}")

    prefix, full_key, key_hash = generate_api_key_material()
    row = ApiKey(
        tenant_id=tenant_id,
        name=name,
        prefix=prefix,
        key_hash=key_hash,
        scopes=scopes,
        created_by=user_id,
        expires_at=expires_at,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)

    quota = await session.get(Quota, tenant_id)
    if quota:
        await _write_cache(row, quota)

    return row, full_key


async def list_api_keys(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    limit: int,
    cursor: str | None,
) -> tuple[list[ApiKey], str | None]:
    q = (
        select(ApiKey)
        .where(ApiKey.tenant_id == tenant_id, ApiKey.revoked_at.is_(None))
        .order_by(ApiKey.created_at.desc(), ApiKey.id.desc())
        .limit(limit + 1)
    )
    if cursor:
        created_at, key_id = decode_cursor(cursor)
        q = q.where(
            (ApiKey.created_at < created_at)
            | ((ApiKey.created_at == created_at) & (ApiKey.id < key_id))
        )

    rows = list(await session.scalars(q))
    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = encode_cursor(last.created_at, last.id)
        rows = rows[:limit]
    return rows, next_cursor


async def revoke_api_key(session: AsyncSession, *, tenant_id: uuid.UUID, key_id: uuid.UUID) -> None:
    row = await session.scalar(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.tenant_id == tenant_id)
    )
    if row is None:
        raise ProblemError(status=404, title="API key not found")
    if row.revoked_at is not None:
        return
    row.revoked_at = datetime.now(UTC)
    await session.commit()
    await evict_api_key_cache(row.key_hash)


async def verify_api_key_hash(session: AsyncSession, *, key_hash: str) -> dict:
    row = await session.scalar(select(ApiKey).where(ApiKey.key_hash == key_hash))
    now = datetime.now(UTC)
    if row is None or row.revoked_at is not None or (row.expires_at and row.expires_at < now):
        raise ProblemError(status=404, title="Unknown, revoked, or expired")

    quota = await session.get(Quota, row.tenant_id)
    if quota is None:
        raise ProblemError(status=404, title="Tenant quota missing")

    row.last_used_at = now
    await session.commit()

    payload = _cache_payload(row, quota)
    await cache_api_key_verification(key_hash, payload)
    return payload


async def _write_cache(row: ApiKey, quota: Quota) -> None:
    await cache_api_key_verification(row.key_hash, _cache_payload(row, quota))


def _cache_payload(row: ApiKey, quota: Quota) -> dict:
    limits = quota_from_model(quota).to_dict()
    return {
        "tenant_id": str(row.tenant_id),
        "key_id": str(row.id),
        "scopes": row.scopes,
        "limits": limits,
    }
