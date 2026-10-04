from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import SessionDep, UserDep
from app.core.quotas import quota_from_model
from app.db.models import Quota, Tenant
from app.schemas.auth import MeOut
from app.schemas.common import QuotaOut

router = APIRouter(tags=["auth"])


@router.get("/v1/me", response_model=MeOut)
async def me(principal: UserDep, session: SessionDep) -> MeOut:
    tenant = await session.get(Tenant, principal.tenant_id)
    quota = await session.get(Quota, principal.tenant_id)
    if tenant is None or quota is None:
        from app.core.errors import ProblemError

        raise ProblemError(status=404, title="Tenant not found")
    q = quota_from_model(quota)
    return MeOut(
        user_id=principal.user_id,
        email=principal.email,
        tenant_id=principal.tenant_id,
        tenant_name=tenant.name,
        role=principal.role,
        quota=QuotaOut(**q.to_dict()),
    )
