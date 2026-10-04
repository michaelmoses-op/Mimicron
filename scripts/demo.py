#!/usr/bin/env python3
"""Seed demo tenant, import heatwave scenario, start accelerated run."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def main() -> None:
    client = httpx.Client(base_url=API, timeout=30.0)
    email = "demo@mimicron.local"
    password = "password1234"
    reg = client.post("/v1/auth/register", json={"email": email, "password": password, "tenant_name": "Demo"})
    if reg.status_code not in (201, 409):
        reg.raise_for_status()
    if reg.status_code == 409:
        login = client.post("/v1/auth/login", json={"email": email, "password": password})
        login.raise_for_status()
        token = login.json()["access_token"]
    else:
        token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    scenario_yaml = (ROOT / "scenarios/examples/smart-building-heatwave.yaml").read_text(encoding="utf-8")
    doc = yaml.safe_load(scenario_yaml)
    created = client.post("/v1/scenarios", headers=headers, json={"scenario": doc, "spec_yaml": scenario_yaml})
    created.raise_for_status()
    scenario_id = created.json()["id"]
    run = client.post(
        "/v1/runs",
        headers=headers,
        json={
            "scenario_id": scenario_id,
            "mode_override": "accelerated",
            "speed_override": 120,
        },
    )
    run.raise_for_status()
    run_id = run.json()["id"]
    print(json.dumps({"scenario_id": scenario_id, "run_id": run_id}, indent=2))
    for _ in range(30):
        time.sleep(2)
        status = client.get(f"/v1/runs/{run_id}", headers=headers).json()["status"]
        print("run status:", status)
        if status in {"completed", "failed", "stopped"}:
            break
    telemetry = client.get(
        "/v1/telemetry",
        headers=headers,
        params={
            "metric": "temperature_c",
            "from": "1970-01-01T00:00:00Z",
            "to": "2099-01-01T00:00:00Z",
            "run_id": run_id,
            "limit": 5,
        },
    )
    print("sample telemetry:", telemetry.json())


if __name__ == "__main__":
    main()
