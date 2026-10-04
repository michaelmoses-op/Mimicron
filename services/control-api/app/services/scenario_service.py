from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.core.quotas import quota_from_model
from app.db.models import Quota, Scenario, ScenarioVersion


def _schema() -> dict[str, Any]:
    from app.core.config import settings

    path = Path(settings.contracts_dir) / "scenario" / "scenario.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


_schema_cache: dict[str, Any] | None = None


def get_scenario_schema() -> dict[str, Any]:
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = _schema()
    return _schema_cache


def parse_scenario_document(raw: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, str):
        doc = yaml.safe_load(raw)
    else:
        doc = raw
    if not isinstance(doc, dict):
        raise ProblemError(status=422, title="Invalid scenario document")
    return doc


def validate_scenario(doc: dict[str, Any], quota: Quota | None) -> tuple[list[dict[str, str]], dict[str, Any]]:
    errors: list[dict[str, str]] = []
    validator = jsonschema.Draft202012Validator(get_scenario_schema())
    for err in validator.iter_errors(doc):
        path = ".".join(str(p) for p in err.path) or "(root)"
        errors.append({"path": path, "code": "schema", "message": err.message})

    estimate = estimate_load(doc)
    if quota is not None:
        q = quota_from_model(quota)
        if estimate["devices"] > q.max_devices:
            errors.append(
                {
                    "path": "spec.fleets",
                    "code": "quota.max_devices",
                    "message": f"device count {estimate['devices']} exceeds quota {q.max_devices}",
                }
            )
        if estimate["events_per_sec"] > q.max_events_per_sec:
            errors.append(
                {
                    "path": "spec",
                    "code": "quota.max_events_per_sec",
                    "message": "estimated events/sec exceeds tenant quota",
                }
            )
    return errors, estimate


def estimate_load(doc: dict[str, Any]) -> dict[str, Any]:
    spec = doc.get("spec", {})
    devices = 0
    eps = 0.0
    for fleet in spec.get("fleets", []):
        count = int(fleet.get("count", 0))
        devices += count
        interval = _parse_duration_seconds(fleet.get("deviceType") and _device_interval(spec, fleet) or "10s")
        if interval > 0:
            metrics = len(_device_metrics(spec, fleet))
            eps += count * metrics / interval
    speed = float(spec.get("time", {}).get("speed", 1) or 1)
    if spec.get("time", {}).get("mode") == "accelerated":
        eps *= speed
    duration_s = _parse_duration_seconds(spec.get("time", {}).get("duration", "3600s"))
    return {
        "devices": devices,
        "events_per_sec": round(eps, 2),
        "total_events": int(eps * duration_s),
    }


def _device_interval(spec: dict[str, Any], fleet: dict[str, Any]) -> str:
    dt = spec.get("deviceTypes", {}).get(fleet.get("deviceType"), {})
    return dt.get("emit", {}).get("interval", "10s")


def _device_metrics(spec: dict[str, Any], fleet: dict[str, Any]) -> dict[str, Any]:
    dt = spec.get("deviceTypes", {}).get(fleet.get("deviceType"), {})
    return dt.get("metrics", {})


def _parse_duration_seconds(raw: str) -> float:
    if not raw:
        return 3600.0
    if raw.endswith("ms"):
        return float(raw[:-2]) / 1000
    for suffix, mult in (("s", 1), ("m", 60), ("h", 3600), ("d", 86400)):
        if raw.endswith(suffix):
            return float(raw[: -len(suffix)]) * mult
    return float(raw)


async def create_scenario(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    doc: dict[str, Any],
    spec_yaml: str | None,
) -> Scenario:
    errors, _ = validate_scenario(doc, await session.get(Quota, tenant_id))
    if errors:
        raise ProblemError(
            status=422,
            title="Validation failed",
            type_="https://mimicron.dev/problems/validation",
            extra={"errors": errors},
        )
    name = doc["metadata"]["name"]
    row = Scenario(
        tenant_id=tenant_id,
        name=name,
        description=doc.get("metadata", {}).get("description"),
        current_version=1,
    )
    session.add(row)
    await session.flush()
    checksum = hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()
    session.add(
        ScenarioVersion(
            scenario_id=row.id,
            version=1,
            spec=doc,
            spec_yaml=spec_yaml or yaml.safe_dump(doc),
            checksum=checksum,
        )
    )
    await session.commit()
    await session.refresh(row)
    return row


async def get_scenario(session: AsyncSession, tenant_id: uuid.UUID, scenario_id: uuid.UUID) -> Scenario:
    row = await session.scalar(
        select(Scenario).where(Scenario.id == scenario_id, Scenario.tenant_id == tenant_id)
    )
    if row is None:
        raise ProblemError(status=404, title="Scenario not found")
    return row


async def get_scenario_version(
    session: AsyncSession, scenario_id: uuid.UUID, version: int
) -> ScenarioVersion:
    row = await session.scalar(
        select(ScenarioVersion).where(
            ScenarioVersion.scenario_id == scenario_id, ScenarioVersion.version == version
        )
    )
    if row is None:
        raise ProblemError(status=404, title="Scenario version not found")
    return row
