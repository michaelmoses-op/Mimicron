# control-api

Python / FastAPI control plane: auth, tenants, API keys, quotas (M1).

## Run locally (with repo infra)

```bash
# from repo root
make infra
cd services/control-api
pip install -e ".[dev]"
export DATABASE_URL=postgresql+asyncpg://mimicron:mimicron_dev@localhost:5432/mimicron
export REDIS_URL=redis://localhost:6379/0
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Or `make up` from repo root (runs migrations in the container entrypoint).

## Test

```bash
pip install -e ".[dev]"
pytest   # integration tests require Docker for testcontainers
ruff check app tests
```

## Config

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Async Postgres (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Key cache + API rate limits |
| `JWT_SECRET` | Access/refresh signing |
| `INTERNAL_API_SECRET` | `X-Internal-Secret` for `/internal/v1/keys/verify` |
