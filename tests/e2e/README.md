# E2E tests

## Compose smoke (`tests/e2e/smoke.py`)

Run against a live stack (`make up`):

```bash
pip install httpx
make e2e
# or: python tests/e2e/smoke.py
```

Flow: wait for health → register tenant → create ingest API key → `POST /v1/ingest` → poll `GET /v1/telemetry` until a point appears.

CI runs the same script in [`.github/workflows/integration.yml`](../../.github/workflows/integration.yml) after `docker compose --profile all up --wait`.

## Full scenario e2e (backlog)

Heat-wave scenario + Timescale row assertions + SSE checks remain in `docs/backlog.md` (M4 follow-up).
