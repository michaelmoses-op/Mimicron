from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status
from sqlalchemy import select

from app.core.deps import ReadDep, SessionDep, UserDep, tenant_id_of
from app.db.models import Quota, Scenario, ScenarioVersion
from app.schemas.scenarios import ScenarioOut, ScenarioPage, ScenarioSummary, ScenarioWrite, ValidationResult
from app.services import scenario_service

router = APIRouter(prefix="/v1", tags=["scenarios"])


@router.post("/scenarios", status_code=status.HTTP_201_CREATED, response_model=ScenarioOut)
async def create_scenario(body: ScenarioWrite, principal: UserDep, session: SessionDep) -> ScenarioOut:
    doc = scenario_service.parse_scenario_document(body.scenario)
    row = await scenario_service.create_scenario(
        session, tenant_id=principal.tenant_id, doc=doc, spec_yaml=body.spec_yaml
    )
    sv = await scenario_service.get_scenario_version(session, row.id, row.current_version)
    return _to_out(row, sv)


@router.post("/scenarios:validate", response_model=ValidationResult)
async def validate_scenario(body: ScenarioWrite, principal: UserDep, session: SessionDep) -> ValidationResult:
    doc = scenario_service.parse_scenario_document(body.scenario)
    quota = await session.get(Quota, principal.tenant_id)
    errors, estimate = scenario_service.validate_scenario(doc, quota)
    return ValidationResult(valid=len(errors) == 0, errors=errors, estimate=estimate)


@router.get("/scenarios/{scenario_id}", response_model=ScenarioOut)
async def get_scenario_route(
    scenario_id: uuid.UUID, principal: ReadDep, session: SessionDep
) -> ScenarioOut:
    row = await scenario_service.get_scenario(session, tenant_id_of(principal), scenario_id)
    sv = await scenario_service.get_scenario_version(session, row.id, row.current_version)
    return _to_out(row, sv)


@router.get("/scenarios", response_model=ScenarioPage)
async def list_scenarios(
    principal: ReadDep,
    session: SessionDep,
    limit: int = Query(50, ge=1, le=500),
) -> ScenarioPage:
    tid = tenant_id_of(principal)
    rows = list(
        await session.scalars(
            select(Scenario)
            .where(Scenario.tenant_id == tid)
            .order_by(Scenario.updated_at.desc())
            .limit(limit)
        )
    )
    return ScenarioPage(
        items=[
            ScenarioSummary(
                id=r.id,
                name=r.name,
                description=r.description,
                current_version=r.current_version,
                updated_at=r.updated_at,
            )
            for r in rows
        ],
        next_cursor=None,
    )


def _to_out(row: Scenario, sv: ScenarioVersion) -> ScenarioOut:
    return ScenarioOut(
        id=row.id,
        name=row.name,
        description=row.description,
        current_version=row.current_version,
        updated_at=row.updated_at,
        spec=sv.spec,
        spec_yaml=sv.spec_yaml,
        checksum=sv.checksum,
    )
