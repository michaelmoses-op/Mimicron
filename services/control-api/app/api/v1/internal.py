from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.deps import SessionDep, verify_internal_secret
from app.schemas.common import QuotaOut
from app.services import api_key_service

router = APIRouter(prefix="/internal/v1", tags=["internal"])


class KeyVerifyRequest(BaseModel):
    key_hash: str = Field(description="hex SHA-256 of the full key")


class KeyVerifyResponse(BaseModel):
    tenant_id: str
    key_id: str
    scopes: list[str]
    limits: QuotaOut


@router.post(
    "/keys/verify",
    response_model=KeyVerifyResponse,
    dependencies=[Depends(verify_internal_secret)],
)
async def verify_key(body: KeyVerifyRequest, session: SessionDep) -> KeyVerifyResponse:
    payload: dict[str, Any] = await api_key_service.verify_api_key_hash(
        session, key_hash=body.key_hash
    )
    return KeyVerifyResponse(
        tenant_id=payload["tenant_id"],
        key_id=payload["key_id"],
        scopes=payload["scopes"],
        limits=QuotaOut(**payload["limits"]),
    )
