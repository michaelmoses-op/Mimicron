from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import UserDep
from app.core.security import create_stream_token
from app.schemas.auth import StreamToken

router = APIRouter(prefix="/v1/stream-tokens", tags=["auth"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=StreamToken)
async def mint_stream_token(principal: UserDep) -> StreamToken:
    token, expires = create_stream_token(
        tenant_id=principal.tenant_id, user_id=principal.user_id
    )
    return StreamToken(token=token, expires_at=expires)
