from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, Response, status

from app.core.deps import SessionDep, UserDep
from app.schemas.api_keys import ApiKeyCreate, ApiKeyCreated, ApiKeyOut, ApiKeyPage
from app.services import api_key_service

router = APIRouter(prefix="/v1/api-keys", tags=["api-keys"])


def _to_out(row) -> ApiKeyOut:
    return ApiKeyOut(
        id=row.id,
        name=row.name,
        prefix=f"mc_live_{row.prefix}",
        scopes=row.scopes,
        created_at=row.created_at,
        last_used_at=row.last_used_at,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
    )


@router.get("", response_model=ApiKeyPage)
async def list_keys(
    principal: UserDep,
    session: SessionDep,
    limit: int = Query(50, ge=1, le=500),
    cursor: str | None = None,
) -> ApiKeyPage:
    rows, next_cursor = await api_key_service.list_api_keys(
        session, tenant_id=principal.tenant_id, limit=limit, cursor=cursor
    )
    return ApiKeyPage(items=[_to_out(r) for r in rows], next_cursor=next_cursor)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiKeyCreated)
async def create_key(
    body: ApiKeyCreate, principal: UserDep, session: SessionDep
) -> ApiKeyCreated:
    row, secret = await api_key_service.create_api_key(
        session,
        tenant_id=principal.tenant_id,
        user_id=principal.user_id,
        name=body.name,
        scopes=list(body.scopes),
        expires_at=body.expires_at,
    )
    out = _to_out(row)
    return ApiKeyCreated(**out.model_dump(), secret=secret)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: uuid.UUID, principal: UserDep, session: SessionDep
) -> Response:
    await api_key_service.revoke_api_key(
        session, tenant_id=principal.tenant_id, key_id=key_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
