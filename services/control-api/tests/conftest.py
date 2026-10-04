from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import docker
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from testcontainers.community.postgres import PostgresContainer
from testcontainers.community.redis import RedisContainer

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def test_infra() -> None:
    try:
        docker.from_env().ping()
    except docker.errors.DockerException as exc:
        pytest.skip(f"Docker required for integration tests: {exc}")
    with PostgresContainer("postgres:16-alpine") as postgres, RedisContainer(
        "redis:7-alpine"
    ) as redis:
        raw = postgres.get_connection_url()
        if raw.startswith("postgresql+psycopg2://"):
            db_url = raw.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        else:
            db_url = raw.replace("postgresql://", "postgresql+asyncpg://", 1)
        redis_url = (
            f"redis://{redis.get_container_host_ip()}:{redis.get_exposed_port(6379)}/0"
        )
        env = os.environ.copy()
        env["DATABASE_URL"] = db_url
        env["REDIS_URL"] = redis_url
        env["JWT_SECRET"] = "test-jwt-secret"
        env["INTERNAL_API_SECRET"] = "test-internal-secret"
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=ROOT,
            check=True,
            env=env,
        )
        os.environ.update(
            {
                "DATABASE_URL": db_url,
                "REDIS_URL": redis_url,
                "JWT_SECRET": "test-jwt-secret",
                "INTERNAL_API_SECRET": "test-internal-secret",
            }
        )
        from app.core.config import settings

        settings.database_url = db_url
        settings.redis_url = redis_url
        settings.jwt_secret = "test-jwt-secret"
        settings.internal_api_secret = "test-internal-secret"
        from app.core.redis_client import close_redis
        from app.db.session import reset_db_engine

        reset_db_engine()
        yield
        import asyncio

        asyncio.run(close_redis())


@pytest_asyncio.fixture
async def client(test_infra: None) -> AsyncGenerator[AsyncClient, None]:
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
