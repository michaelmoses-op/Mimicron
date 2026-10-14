from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_key_scopes_read_vs_simulate(client: AsyncClient) -> None:
    reg = await client.post(
        "/v1/auth/register",
        json={"email": "scopes@example.com", "password": "password1234"},
    )
    assert reg.status_code == 201
    access = reg.json()["access_token"]

    read_key = await client.post(
        "/v1/api-keys",
        headers={"Authorization": f"Bearer {access}"},
        json={"name": "read-only", "scopes": ["read"]},
    )
    assert read_key.status_code == 201
    read_secret = read_key.json()["secret"]

    usage = await client.get("/v1/usage", headers={"X-API-Key": read_secret})
    assert usage.status_code == 200

    scenarios = await client.get("/v1/scenarios", headers={"X-API-Key": read_secret})
    assert scenarios.status_code == 200

    denied = await client.post(
        "/v1/runs",
        headers={"X-API-Key": read_secret},
        json={"scenario_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert denied.status_code == 403

    stream = await client.post("/v1/stream-tokens", headers={"X-API-Key": read_secret})
    assert stream.status_code == 201

    sim_key = await client.post(
        "/v1/api-keys",
        headers={"Authorization": f"Bearer {access}"},
        json={"name": "sim", "scopes": ["simulate"]},
    )
    assert sim_key.status_code == 201
    sim_secret = sim_key.json()["secret"]

    no_read = await client.get("/v1/usage", headers={"X-API-Key": sim_secret})
    assert no_read.status_code == 403

    stream_denied = await client.post("/v1/stream-tokens", headers={"X-API-Key": sim_secret})
    assert stream_denied.status_code == 403
