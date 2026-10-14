#!/usr/bin/env python3
"""Compose e2e smoke: register, API key, ingest, assert telemetry via control-api."""
from __future__ import annotations

import os
import sys
import time
import uuid
from datetime import datetime, timezone

import httpx

API = os.environ.get("CONTROL_API_URL", "http://localhost:8000").rstrip("/")
INGEST = os.environ.get("INGEST_URL", "http://localhost:8081").rstrip("/")
WAIT_SEC = int(os.environ.get("E2E_WAIT_SEC", "300"))


def wait_ok(base: str, path: str = "/healthz") -> None:
    deadline = time.time() + WAIT_SEC
    url = f"{base}{path}"
    while time.time() < deadline:
        try:
            r = httpx.get(url, timeout=5.0)
            if r.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(3)
    print(f"timeout: {url}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    wait_ok(API)
    wait_ok(INGEST)
    email = f"e2e-{uuid.uuid4().hex[:8]}@mimicron.local"
    password = "password1234"
    with httpx.Client(timeout=30.0) as client:
        reg = client.post(
            f"{API}/v1/auth/register",
            json={"email": email, "password": password, "tenant_name": "E2E"},
        )
        if reg.status_code != 201:
            print(reg.text, file=sys.stderr)
            reg.raise_for_status()
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        key = client.post(
            f"{API}/v1/api-keys",
            headers=headers,
            json={"name": "e2e-ingest", "scopes": ["ingest", "read"]},
        )
        key.raise_for_status()
        secret = key.json()["secret"]
        now = datetime.now(timezone.utc).isoformat()
        ingest = client.post(
            f"{INGEST}/v1/ingest",
            headers={"X-API-Key": secret, "Content-Type": "application/json"},
            json={
                "events": [
                    {
                        "device_id": "e2e-device-1",
                        "event_time": now,
                        "data": {"temperature_c": 42.0},
                    }
                ]
            },
        )
        if ingest.status_code != 202:
            print(ingest.text, file=sys.stderr)
            ingest.raise_for_status()
        deadline = time.time() + 90
        found = False
        while time.time() < deadline:
            tel = client.get(
                f"{API}/v1/telemetry",
                headers=headers,
                params={
                    "metric": "temperature_c",
                    "from": "1970-01-01T00:00:00Z",
                    "to": "2099-01-01T00:00:00Z",
                    "device_id": "e2e-device-1",
                    "limit": 1,
                },
            )
            tel.raise_for_status()
            items = tel.json().get("items") or []
            if items:
                found = True
                break
            time.sleep(3)
        if not found:
            print("telemetry not visible after ingest", file=sys.stderr)
            sys.exit(1)
    print("e2e smoke ok")


if __name__ == "__main__":
    main()
