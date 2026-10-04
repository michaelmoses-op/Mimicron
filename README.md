# Mimicron

Multi-tenant platform for **simulated device fleets and synthetic traffic** ("Twilio for fake telemetry"). Developers define scenarios in YAML, run simulations, and consume data via REST, SSE, and a dashboard.

## Docs

| Resource | Path |
|----------|------|
| Architecture | [docs/architecture.md](docs/architecture.md) |
| Scenario language | [docs/scenario-spec.md](docs/scenario-spec.md) |
| Repo layout | [docs/repo-layout.md](docs/repo-layout.md) |
| Agent / milestone guide | [AGENTS.md](AGENTS.md) |
| Contracts | [contracts/](contracts/) |

## Prerequisites

- Docker Desktop (Compose v2)
- Make (optional on Windows: run equivalent `docker compose` commands)
- For local tests: Python 3.12, Go 1.23, Rust stable, Node 22

## Quick start

```bash
cp .env.example .env
make infra    # Postgres, Timescale, Redis, Redpanda, MinIO + topic/bucket/migrate init
make up       # infra + service stubs (health endpoints)
make contracts
make test
```

Service ports: control-api `8000`, ingestion-gateway `8081`, stream-gateway `8082`, Redpanda Kafka `19092`, Timescale `5433`.

## Milestone status

- **M0 (foundation):** monorepo skeleton, infra compose, contracts validation, Timescale migrations, CI
- **M1 (control-api identity/keys):** auth, API keys, Alembic, Redis cache/rate limits — see `services/control-api`
- **M2+:** see [AGENTS.md](AGENTS.md)
