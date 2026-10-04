from __future__ import annotations

from fastapi import APIRouter, status

from app.core.config import settings
from app.core.deps import SessionDep
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair
from app.services import auth_service

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenPair)
async def register(body: RegisterRequest, session: SessionDep) -> TokenPair:
    _user, _tenant, _membership, access, refresh = await auth_service.register_user(
        session, email=body.email, password=body.password, tenant_name=body.tenant_name
    )
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_ttl_seconds,
    )


@router.post("/login", response_model=TokenPair)
async def login(body: LoginRequest, session: SessionDep) -> TokenPair:
    _user, _tenant, _membership, access, refresh = await auth_service.login_user(
        session, email=body.email, password=body.password
    )
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_ttl_seconds,
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest, session: SessionDep) -> TokenPair:
    access, refresh_token = await auth_service.refresh_tokens(
        session, refresh_token=body.refresh_token
    )
    return TokenPair(
        access_token=access,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_ttl_seconds,
    )

