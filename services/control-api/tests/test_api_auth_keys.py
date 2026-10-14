from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.security import hash_api_key


@pytest.mark.asyncio
async def test_register_login_me_and_api_keys(client: AsyncClient) -> None:
    reg = await client.post(
        "/v1/auth/register",
        json={"email": "dev@example.com", "password": "password1234", "tenant_name": "Acme"},
    )
    assert reg.status_code == 201, reg.text
    tokens = reg.json()
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]

    me = await client.get("/v1/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "dev@example.com"
    assert body["tenant_name"] == "Acme"
    assert body["quota"]["max_devices"] == 500

    login = await client.post(
        "/v1/auth/login",
        json={"email": "dev@example.com", "password": "password1234"},
    )
    assert login.status_code == 200

    rotated = await client.post("/v1/auth/refresh", json={"refresh_token": refresh})
    assert rotated.status_code == 200
    access2 = rotated.json()["access_token"]

    created = await client.post(
        "/v1/api-keys",
        headers={"Authorization": f"Bearer {access2}"},
        json={"name": "ingest-key", "scopes": ["ingest", "read"]},
    )
    assert created.status_code == 201
    key_body = created.json()
    secret = key_body["secret"]
    key_id = key_body["id"]
    assert secret.startswith("mc_live_")

    listed = await client.get(
        "/v1/api-keys",
        headers={"Authorization": f"Bearer {access2}"},
    )
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    verify = await client.post(
        "/internal/v1/keys/verify",
        headers={"X-Internal-Secret": "test-internal-secret"},
        json={"key_hash": hash_api_key(secret)},
    )
    assert verify.status_code == 200
    assert verify.json()["scopes"] == ["ingest", "read"]

    revoked = await client.delete(
        f"/v1/api-keys/{key_id}",
        headers={"Authorization": f"Bearer {access2}"},
    )
    assert revoked.status_code == 204

    verify2 = await client.post(
        "/internal/v1/keys/verify",
        headers={"X-Internal-Secret": "test-internal-secret"},
        json={"key_hash": hash_api_key(secret)},
    )
    assert verify2.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_register_conflict(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "password": "password1234"}
    assert (await client.post("/v1/auth/register", json=payload)).status_code == 201
    dup = await client.post("/v1/auth/register", json=payload)
    assert dup.status_code == 409
    assert dup.headers["content-type"].startswith("application/problem+json")
