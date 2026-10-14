# Mimicron

Multi-tenant platform for **simulated device fleets and synthetic traffic** ("Twilio for fake telemetry"). Developers define scenarios in YAML, run simulations, and consume data via REST, SSE, and a dashboard.

## Docs

| Resource | Path |
|----------|------|
| Architecture | [docs/architecture.md](docs/architecture.md) |
| Scenario language | [docs/scenario-spec.md](docs/scenario-spec.md) |
| Repo layout | [docs/repo-layout.md](docs/repo-layout.md) |
| Agent / milestone guide | [AGENTS.md](AGENTS.md) |
| CI/CD & releases | [docs/ci.md](docs/ci.md) |
| Deployment | [docs/deployment.md](docs/deployment.md) |
| Observability | [docs/observability.md](docs/observability.md) |
| Contracts | [contracts/](contracts/) |

## Prerequisites

- Docker Desktop (Compose v2)
- Make (optional on Windows: run equivalent `docker compose` commands)
- For local tests: Python 3.12, Go 1.23, Rust stable, Node 22

## Quick start

```bash
cp .env.example .env
make infra    # Postgres, Timescale, Redis, Redpanda, object store + topic/bucket/migrate init
make up       # infra + all services
make contracts
make test
```

Service ports: control-api `8000`, ingestion-gateway `8081`, stream-gateway `8082`, Redpanda Kafka `19092`, Timescale `5433`, S3-compatible API `9000`.

**Object storage:** Local compose runs an **S3-compatible** server (`object-store` service). Official MinIO Docker images were removed from Docker Hub; we use **RustFS** as a API-compatible stand-in until MinIO images are available again. Configure with `S3_ENDPOINT`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_FORCE_PATH_STYLE` (see `.env.example`). The same variables work with Cloudflare R2, Backblaze B2, DigitalOcean Spaces, GCS interoperability, or AWS S3. During `make infra`, `object-store-init` prints that the archive bucket is ready — normal for a later replay milestone; the live demo does not use it yet.

**Deployment stance:** First production target is **Docker Compose on a generic Linux VM** (any provider). See [ADR 0007](docs/adr/0007-cloud-neutral-deployment.md).

## Milestone status

- **M0 (foundation):** monorepo skeleton, infra compose, contracts validation, Timescale migrations, CI
- **M1 (control-api identity/keys):** auth, API keys, Alembic, Redis cache/rate limits
- **M2 (ingestion-gateway):** `POST /v1/ingest`, auth, rate limit, Kafka publish
- **M3 (stream-processor):** consume `telemetry.raw`, dedupe, Timescale sink, EWMA/stuck/dropout detectors → `anomalies` + `anomalies.detected`
- **M4 (sim + scenarios/runs):** control-api scenarios/runs/telemetry, sim-engine, `make demo`
- **M5 (dashboard + SSE):** SvelteKit UI on `:5173`, stream-gateway SSE on `:8082`, scenarios/runs/traffic, API keys, usage, anomalies pages
- **M6 (traffic):** sim-engine traffic profiles + `scale_traffic`, stream-processor `traffic_rollups_10s`, `GET /v1/traffic`, dashboard `/traffic` (see `docs/backlog.md` for M6 follow-ups)
- **M7 (CI/CD):** path-filtered unit CI, Compose integration + k6, GHCR image publish — [docs/ci.md](docs/ci.md)
- **M8 (observability + deploy):** Prometheus/Grafana/Jaeger/OTel, Caddy prod overlay, VM bootstrap notes — [docs/observability.md](docs/observability.md), [docs/deployment.md](docs/deployment.md)
- **Portfolio follow-ups:** fill [docs/load-test-results.md](docs/load-test-results.md); deeper OTel in all services (`docs/backlog.md`)
- **Smoke test:** [tests/e2e/INGEST.md](tests/e2e/INGEST.md) or `make demo` after `make up`

## External developers (API keys)

1. Register in the dashboard (`/login`) or `POST /v1/auth/register`.
2. Create scoped keys on **API keys** (`/api-keys`): e.g. `ingest` for `POST /v1/ingest`, `read` for queries and SSE, `simulate` for runs, `admin` for all machine scopes.
3. Ingest: `Authorization: Bearer mc_live_…` or `X-API-Key` on ingestion-gateway `:8081`.
4. Query: same key on control-api `:8000` for `/v1/telemetry`, `/v1/traffic`, `/v1/anomalies`, `/v1/usage`, `/v1/scenarios` (read), `/v1/runs` (read list/get).
5. Runs: key with `simulate` for `POST /v1/runs` and stop/pause/resume.
6. Live stream: `POST /v1/stream-tokens` with a `read` key, then `GET /v1/stream?token=…` on stream-gateway `:8082` (API keys with `read` also work directly).

Human-only (JWT): create/revoke API keys, create scenarios, account `/v1/me`.

Set strong `JWT_SECRET` and `INTERNAL_API_SECRET` in `.env` before exposing the stack.
