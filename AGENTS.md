# MASTER PROMPT FOR CURSOR (paste into the first Agent chat, or save as `AGENTS.md`)

You are my senior engineering partner building **Mimicron**, a portfolio-grade, production-style platform. I will work only through you from here on, so follow this document precisely. Everything you need is in this prompt and the files in this repo: `docs/`, `contracts/`, `scenarios/`, `.cursor/rules/00-project.mdc`. **Read all of them before writing code.**

## 1. What we are building

A multi-tenant cloud platform ("Twilio for fake telemetry") where developers:
1. Define **scenarios** in YAML (virtual device fleets, synthetic customer/network traffic, scheduled events, injected anomalies).
2. Run them as **simulations** that emit realistic, deterministic, seeded data through the platform's public ingestion API.
3. Consume the results via **REST queries**, **SSE streams**, and a dashboard, to build their own IoT dashboards, anomaly detectors, ETL pipelines, or ML projects.

It also accepts data from real external sources via the same ingestion API.

**Purpose:** a software-engineer portfolio project that mimics a production environment: microservices, polyglot services, multiple datastores, streaming pipelines, CI/CD, observability, public APIs, multi-tenancy, and documentation. Depth and correctness in the core path matter more than breadth. Quality bar: something I can defend line by line in a senior interview.

## 2. Decisions that are FINAL (do not relitigate or deviate)

- **Services and languages**
  - `control-api`: **Python / FastAPI** (auth, tenants, API keys, quotas, scenarios, runs, telemetry query API, usage)
  - `sim-engine`: **Go** (device simulator and traffic simulator share one scenario runtime)
  - `ingestion-gateway`: **Go**
  - `stream-processor`: **Rust**. This is the **only** Rust service. It does validation, dedupe, batch writes to TimescaleDB, anomaly detection, traffic rollups.
  - `stream-gateway`: **Node / Express / TypeScript** (SSE fan-out; WebSocket later)
  - `dashboard`: **SvelteKit** (Svelte 5, TypeScript, Tailwind)
- **Datastores:** PostgreSQL (metadata), TimescaleDB (telemetry; separate instance), Redis (key cache, rate limits, usage counters), MinIO/S3 (later: archives/replay). **No Cassandra. No other databases** unless I explicitly approve.
- **Messaging:** Redpanda (Kafka API). Topics: `sim.commands`, `sim.events`, `telemetry.raw`, `telemetry.processed`, `anomalies.detected`, `telemetry.dlq`.
- **Monorepo** with layout in `docs/repo-layout.md`.
- **Contract-first:** `/contracts` holds OpenAPI (`control-api.yaml`, `data-plane.yaml`), the scenario JSON Schema, and event definitions. Code follows contracts.
- **Dogfooding:** the simulator sends data through the public ingestion gateway like any external device, using a short-lived run token.
- **Auth:** JWT for humans; API keys (`mc_live_<prefix>_<secret>`, SHA-256 hashed at rest, scopes `ingest|read|simulate|admin`) for machines; run tokens for the simulator; short-lived stream tokens for SSE. Gateways verify keys via Redis cache with fallback to `POST /internal/v1/keys/verify`.
- **Telemetry storage model:** narrow table `measurements(time, ingest_time, tenant_id, run_id, device_id, metric, value)`, hypertable, idempotent primary key, compression and retention policies, 1m/1h continuous aggregates.
- **Delivery semantics:** at-least-once with idempotent sinks.
- **Determinism:** same scenario + seed + virtual start => same events (per-device PRNG derived from the seed).

## 3. Source-of-truth files (read these first)

| File | What it defines |
|---|---|
| `docs/architecture.md` + `docs/architecture.mermaid` | Services, flows, auth model, DB schemas (Postgres and Timescale DDL), topics, event envelope, anomaly detectors |
| `docs/scenario-spec.md` + `contracts/scenario/scenario.schema.json` | Scenario language, generators, timeline actions, traffic profiles, validation rules |
| `scenarios/examples/smart-building-heatwave.yaml` | Canonical example, used as the e2e and demo fixture |
| `contracts/openapi/control-api.yaml` | Control API endpoints and schemas |
| `contracts/openapi/data-plane.yaml` | `POST /v1/ingest` and `GET /v1/stream` |
| `docs/repo-layout.md` | Directory structure, ports, Makefile targets, conventions |
| `.cursor/rules/00-project.mdc` | Coding rules (always on) |

If these files conflict with each other, tell me, propose the fix, and update the file. If something is missing (for example `contracts/events/envelope.schema.json` and `topics.md`), create it from `docs/architecture.md` as your first task.

## 4. Later features (design for them now, build them later)

1. **Chaos / fault injection** (drop, duplicate, delay/late/out-of-order, clock skew, schema drift, corrupt). It will live in `sim-engine/internal/chaos` as emitter middleware; the scenario schema already reserves `spec.chaos`. For now: define the Go interface and a no-op implementation, and make sure events carry `event_id` and `seq` so chaos effects are detectable downstream.
2. **Time travel / replay:** stream-processor archives Parquet to MinIO; sim-engine gets a replay source. Scenario `time.mode` already supports `accelerated` and `backfill`. Implement `accelerated` and `backfill` in the virtual clock from the start (they are just clock behavior).
3. **Reference app:** a small app under `/examples` built only on the public API/SDK (for example an anomaly monitor that evaluates detector precision/recall against ground-truth labels).
Not planned: Kubernetes/GitOps (first target is Docker Compose plus Terraform on a single VM), Cassandra, billing, multi-region.

## 5. Build order (milestones)

Work **one milestone at a time**. At the end of each: summarize what you built, how to run and test it, what to review, and wait for my go-ahead before the next one. Each milestone must leave the repo in a working state (`make up`, `make test`, CI green).

**M0: Foundation**
- Create the monorepo skeleton per `docs/repo-layout.md` (empty service stubs with Dockerfiles, health endpoints, READMEs).
- `docker-compose.yml`: Redpanda (+ Console), Postgres, TimescaleDB, Redis, MinIO; init containers that create topics and buckets; `.env.example`; `Makefile`.
- Create `contracts/events/envelope.schema.json` and `topics.md`.
- Timescale migrations from `docs/architecture.md` section 5.2 plus a tiny migration runner.
- CI skeleton with path-filtered lint/test jobs per service; a contracts job that validates the OpenAPI files and the JSON Schema (and validates the example scenario against the schema).
- ADRs 0001 through 0006.
- Done when: `make infra` is healthy; CI is green on the skeleton.

**M1: control-api core (identity and keys)**
- Alembic migrations for the Postgres schema. Register/login/refresh/me, tenants, memberships, quotas (defaults per tier), API key create/list/revoke, internal key-verify endpoint, Redis key cache write-through and eviction on revoke, problem+json errors, request IDs, structured logging, Redis-based API rate limiting, `/healthz` `/readyz` `/metrics`.
- Tests: unit + API tests with testcontainers + contract test comparing the live OpenAPI output to `contracts/openapi/control-api.yaml`.

**M2: ingestion-gateway (Go)**
- Implement `POST /v1/ingest` per `data-plane.yaml`: auth (API key and run token), scope check, Redis token-bucket rate limiting (Lua), envelope validation with per-event error reporting, server-side stamping of `tenant_id`/`ingest_time`, publish to `telemetry.raw` keyed `{tenant_id}:{device_id}`, usage counters in Redis (flushed to `usage_daily` by control-api every minute).
- Tests: unit, handler tests, integration with Redpanda and Redis. Include a k6 smoke script.

**M3: stream-processor (Rust)**
- Consume `telemetry.raw` in batches; validate; dedupe (bounded window by `event_id`); batch-write `measurements` and upsert `devices` into Timescale (idempotent); commit offsets after flush; failures to `telemetry.dlq` with reason header; publish `telemetry.processed`.
- Detectors behind a `Detector` trait: EWMA + z-score, stuck-value, dropout. Publish `anomalies.detected` and write `anomalies` rows.
- Metrics: consumer lag, batch size, flush latency, events/sec, anomalies/sec. Graceful shutdown.
- Tests: detector unit tests on synthetic series; integration test with Redpanda + Timescale.

**M4: sim-engine (Go) + scenarios and runs**
- Scenario pipeline: parse YAML, JSON-Schema validate, semantic validate (rules in `docs/scenario-spec.md`), compile to an execution plan.
- Virtual clock (realtime/accelerated/backfill), seeded per-device PRNG, generators (constant, sine, random_walk, gaussian, uniform, linear, sawtooth, steps), noise/bounds/precision, fleet variance, jitter, timeline actions (`adjust`, `set_state`, `inject_anomaly`, `set_rate`), ground-truth labels to `sim.events`, HTTP batch emitter with retry/backoff and backpressure, goroutine-per-device worker pool, consume `sim.commands`, publish run status to `sim.events`, graceful stop, per-run metrics.
- control-api: scenarios CRUD with versioning + validate endpoint (with load estimate), runs (start/stop/pause/resume), quota enforcement, run-token minting, `sim.events` consumer updating `runs` and `ground_truth_labels`, telemetry/anomaly/device/usage query endpoints (read-only Timescale role, tenant-filtered, cursor pagination).
- Tests: determinism test (same seed => identical event stream), generator unit tests, validation tests, an e2e test in `tests/e2e` running the example scenario and asserting rows in Timescale.
- Done when: `make demo` seeds a tenant, starts the heat-wave scenario, and data is queryable via the API.

**M5: stream-gateway + dashboard**
- stream-gateway (Express/TS): SSE with auth (key, bearer, stream token), tenant + query filters, heartbeats, per-tenant connection limits, `Last-Event-ID` best-effort resume, metrics.
- control-api: `POST /v1/stream-tokens`.
- Dashboard (SvelteKit): login/register, API key manager (secret shown once), scenario editor with live validation + load estimate, run list/detail with start/stop/pause, **live charts** (SSE + uPlot), anomaly feed with ground-truth overlay, usage page. Generate the API client from OpenAPI. Clean, minimal design; responsive; dark mode.

**M6: traffic simulator**
- Poisson arrivals with diurnal/spiky patterns, sessions, flows/steps, latency/error/bytes distributions, regions, `scale_traffic` action; `kind: traffic` events; stream-processor 10s rollups into `traffic_rollups_10s`; dashboard traffic view (RPS, error rate, p50/p95/p99).

**M7: CI/CD hardening**
- GitHub Actions: lint, test (race detector for Go), build, image scan (Trivy), SBOM, push to GHCR on main, compose-based e2e job, k6 load test job with thresholds. Dependabot. Version/tag strategy. Branch protection notes in docs.

**M8: Observability and deployment**
- OpenTelemetry tracing across HTTP and Kafka headers, Prometheus metrics, Grafana dashboards (per-service RED + pipeline lag + platform SLOs), Terraform for a single-VM deployment with Compose (TLS via Caddy), staging/prod environments, public status page, README with architecture diagram, demo GIF script, and a published load-test result.

**Then (when I ask):** chaos/fault injection, time travel/replay, reference app, SDKs (Python, TypeScript), webhooks.

## 6. How to work with me

- **Plan before you code.** At the start of each milestone, give a short plan (files to create, key design choices, anything ambiguous) and proceed unless I object. Keep plans under ~25 lines.
- **Ask when it matters.** One concise question if a decision is not covered by the docs; otherwise make the sensible choice, state it, and record it in an ADR if significant.
- **Do not expand scope** beyond the current milestone. If you see a better idea, add it to `docs/backlog.md` and mention it at the end.
- **Quality gates:** tests for new logic, lint/format clean, no secrets in code, contracts updated, READMEs updated, `make up` works.
- **Be honest about problems.** If something fails or is incomplete, say so plainly and propose the fix instead of papering over it.
- **Explain tradeoffs briefly** in code review summaries, because I need to defend each decision in interviews. Keep ADRs short: Context, Decision, Consequences.
- **Performance targets to design for** (verify in M7/M8): ingestion gateway sustained 5,000 events/sec on a small VM with p99 < 50 ms ack latency; stream-processor end-to-end latency (gateway ack to row visible) p95 < 2 s; sim-engine at least 1,000 devices at 1 Hz per core.

## 7. First task

1. Read every file listed in section 3.
2. Reply with: (a) a 10-line summary of your understanding of the system, (b) any contradictions or gaps you found in the docs/contracts, (c) the M0 plan.
3. After my go-ahead, implement M0.
