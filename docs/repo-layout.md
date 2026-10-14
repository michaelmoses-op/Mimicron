# Repo Layout

Monorepo. Each service is independently buildable, testable, and containerized. Shared contracts live under `contracts/`.

```
mimicron/
├── README.md
├── Makefile                      # single entry point: make up, test, lint, e2e, load
├── docker-compose.yml            # infra + all services (profiles: infra, services, obs)
├── docker-compose.dev.yml        # hot-reload overrides
├── .env.example
├── .gitignore
├── .editorconfig
├── .cursor/rules/                # Cursor project rules (see 00-project.mdc)
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                # path-filtered per-service jobs: lint, test, build, trivy
│   │   ├── contracts.yml         # validate OpenAPI + JSON Schema, contract tests
│   │   ├── e2e.yml               # compose up, run scenario, assert data lands
│   │   └── release.yml           # build/push images to GHCR, deploy
│   └── dependabot.yml
│
├── contracts/                    # SOURCE OF TRUTH. Change here first.
│   ├── openapi/
│   │   ├── control-api.yaml
│   │   └── data-plane.yaml
│   ├── scenario/
│   │   └── scenario.schema.json
│   └── events/
│       ├── envelope.schema.json  # Kafka event envelope (derive from docs/architecture.md section 6)
│       └── topics.md             # topic names, keys, retention, partitions
│
├── services/
│   ├── control-api/              # Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2
│   │   ├── pyproject.toml        # uv or poetry; ruff + mypy + pytest
│   │   ├── Dockerfile
│   │   ├── alembic/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── api/v1/           # routers: auth, api_keys, scenarios, runs, telemetry, usage, internal
│   │   │   ├── core/             # config, security (JWT, hashing), errors (problem+json), ratelimit, logging, otel
│   │   │   ├── db/               # engine, session, models
│   │   │   ├── schemas/          # Pydantic request/response models
│   │   │   ├── services/         # business logic: scenarios (validation), runs, quotas, keys, usage
│   │   │   ├── timescale/        # read-only query layer for telemetry
│   │   │   └── messaging/        # Redpanda producer (sim.commands), consumer (sim.events)
│   │   └── tests/                # unit, api (httpx + testcontainers), contract
│   │
│   ├── sim-engine/               # Go 1.23
│   │   ├── go.mod
│   │   ├── Dockerfile
│   │   ├── cmd/sim-engine/main.go
│   │   └── internal/
│   │       ├── scenario/         # parse, schema-validate, semantic-validate, compile to plan
│   │       ├── runtime/          # run manager, scheduler (virtual clock), device worker, traffic worker
│   │       ├── generators/       # constant, sine, random_walk, gaussian, uniform, linear, sawtooth, steps
│   │       ├── rng/              # seeded per-device PRNG derivation
│   │       ├── emitters/         # http batch emitter (MQTT/WebSocket later)
│   │       ├── chaos/            # emitter middleware (later milestone; stub interface now)
│   │       ├── bus/              # sim.commands consumer, sim.events producer
│   │       └── telemetry/        # metrics, tracing
│   │
│   ├── ingestion-gateway/        # Go 1.23
│   │   ├── cmd/ingestion-gateway/main.go
│   │   └── internal/
│   │       ├── auth/             # key hash, Redis cache, control-api fallback, run-token verify
│   │       ├── ratelimit/        # Redis token bucket (Lua script)
│   │       ├── validate/         # envelope validation
│   │       ├── producer/         # Redpanda producer
│   │       ├── usage/            # Redis counters
│   │       └── http/             # handlers, middleware
│   │
│   ├── stream-processor/         # Rust (stable), tokio, rdkafka, sqlx, serde, tracing, metrics
│   │   ├── Cargo.toml
│   │   ├── Dockerfile
│   │   └── src/
│   │       ├── main.rs
│   │       ├── config.rs
│   │       ├── consumer.rs       # batching, offset commit after flush
│   │       ├── model.rs          # envelope types
│   │       ├── dedupe.rs
│   │       ├── sink/             # timescale batch writer (COPY or UNNEST inserts), device registry upserts
│   │       ├── detectors/        # trait Detector; ewma_zscore, stuck_value, dropout
│   │       ├── rollups.rs        # traffic 10s windows
│   │       └── publish.rs        # processed / anomalies / dlq
│   │
│   └── stream-gateway/           # Node 22, Express, TypeScript, kafkajs, ioredis
│       ├── package.json
│       ├── tsconfig.json
│       ├── Dockerfile
│       └── src/
│           ├── index.ts
│           ├── auth.ts           # key / stream-token verification (Redis, fallback to control-api)
│           ├── sse.ts            # connection registry, filters, heartbeats
│           ├── consumer.ts       # one shared consumer group per instance, fan-out in memory
│           └── metrics.ts
│   (each service has its own tests/ or *_test files and a README with run instructions)
│
├── dashboard/                    # SvelteKit (TypeScript), Tailwind, Svelte 5 runes
│   ├── package.json
│   ├── Dockerfile
│   └── src/
│       ├── lib/
│       │   ├── api/              # client generated from contracts/openapi via openapi-typescript
│       │   ├── stores/           # session, live stream stores
│       │   └── components/       # charts (uPlot or Chart.js), tables, scenario editor, key manager
│       └── routes/
│           ├── (auth)/login, register
│           ├── (app)/overview
│           ├── (app)/scenarios, scenarios/[id]
│           ├── (app)/runs, runs/[id]         # live charts + anomalies + ground-truth overlay
│           ├── (app)/api-keys
│           ├── (app)/usage
│           └── docs/                          # embeds developer portal content (later)
│
├── db/
│   └── timescale/
│       ├── migrations/           # numbered .sql files, applied by a small runner container
│       └── README.md
│
├── scenarios/
│   └── examples/                 # smart-building-heatwave.yaml, ev-charging.yaml, api-traffic.yaml
│
├── infra/
│   ├── docker/                   # init scripts (redpanda topics, S3-compatible bucket)
│   ├── observability/            # prometheus.yml, grafana dashboards, otel-collector.yaml
│   ├── terraform/                # modules/ (network, vm, object-storage); providers/<name>/ roots
│   └── k8s/                      # later (kustomize / helm + ArgoCD)
│
├── tests/
│   ├── e2e/                      # run example scenario, assert rows in Timescale + SSE events
│   └── load/                     # k6 scripts against ingestion-gateway and control-api
│
├── sdk/                          # later
│   ├── python/
│   └── typescript/
├── examples/                     # later: reference apps built only on the public API/SDK
│   └── anomaly-monitor/
└── docs/
    ├── architecture.md
    ├── architecture.mermaid
    ├── scenario-spec.md
    ├── repo-layout.md
    ├── runbook.md                # local dev, debugging, common failures
    └── adr/
        ├── 0001-monorepo.md
        ├── 0002-redpanda-over-kafka.md
        ├── 0003-timescale-for-telemetry.md
        ├── 0004-rust-only-for-stream-processor.md
        ├── 0005-narrow-measurement-schema.md
        ├── 0006-no-cassandra.md
        ├── 0007-cloud-neutral-deployment.md
        ├── 0008-ci-ghcr-trivy.md
        └── 0009-observability-and-edge.md
```

## Ports (local)

| Service | Port |
|---|---|
| control-api | 8000 |
| ingestion-gateway | 8081 |
| stream-gateway | 8082 |
| dashboard | 5173 (dev) / 3000 (prod) |
| Postgres (metadata) | 5432 |
| TimescaleDB | 5433 |
| Redis | 6379 |
| Redpanda (Kafka API / Console) | 19092 / 8080 |
| S3-compatible object storage (API / console) | 9000 / 9001 |
| Prometheus / Grafana | 9090 / 3001 |

## Makefile targets (minimum)

`make up` (infra + services), `make infra`, `make down`, `make logs`, `make migrate`, `make test` (all), `make test-<service>`, `make lint`, `make contracts` (validate specs), `make gen-client` (dashboard TS client from OpenAPI), `make seed` (demo tenant, API key, example scenario), `make demo` (seed and start the example run), `make e2e`, `make load`.

## Conventions

- Env config only via environment variables (12-factor); every variable documented in `.env.example`.
- Every service exposes `/healthz`, `/readyz`, `/metrics` (Prometheus), and logs JSON to stdout with `request_id`, `tenant_id`, `trace_id`.
- Conventional Commits; trunk-based development with short-lived branches; CI must pass to merge.
- Any change to a public contract updates `/contracts` in the same PR, plus an ADR if it is a decision (not just a field addition).
