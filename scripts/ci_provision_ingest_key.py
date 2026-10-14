#!/usr/bin/env python3
"""Print a one-off ingest API key secret for CI (register + create key)."""
from __future__ import annotations

import sys
import uuid

import httpx

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def main() -> None:
    email = f"ci-{uuid.uuid4().hex[:8]}@mimicron.local"
    password = "password1234"
    with httpx.Client(base_url=API, timeout=30.0) as client:
        reg = client.post(
            "/v1/auth/register",
            json={"email": email, "password": password, "tenant_name": "CI"},
        )
        reg.raise_for_status()
        token = reg.json()["access_token"]
        key = client.post(
            "/v1/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "ci-k6", "scopes": ["ingest"]},
        )
        key.raise_for_status()
        print(key.json()["secret"], end="")


if __name__ == "__main__":
    main()
