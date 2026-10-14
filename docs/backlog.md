# Backlog (post M8 slice)

## M8 follow-ups

- Full OTel SDK in Go/Rust services; stream-processor consume traceparent from Kafka
- Prometheus metrics on all services (RED); consumer lag gauge
- Automated status page (blackbox checks); Loki optional
- Real provider Terraform (Hetzner/DO) calling generic modules
- Record demo GIF and fill `docs/load-test-results.md`

# Backlog (post M7 slice)

## M7 follow-ups

- Cosign image signing; richer GHA layer caching for Rust/Go
- Path-filter `integration.yml` on PRs (docs-only PRs skip Compose)
- Pin Trivy allowlist if base-image CVEs block `main` publishes

# Backlog (post M6 slice)

## M6 follow-ups

- Merge percentile stats correctly on rollup upsert (t-digest / reservoir) instead of last-batch overwrite
- Virtual-clock timeline for device + traffic (scale_traffic at scenario `at:` offsets in accelerated runs)
- Dedicated `scenarios/examples/api-traffic.yaml` smoke with low rate for CI

# Backlog (post M4/M5 slice)

Items deferred from AGENTS milestones; not blocking local demo.

## M3 stream-processor

- Anomaly detectors (EWMA, stuck-value, dropout) and `anomalies.detected`
- DLQ with reason headers; Prometheus metrics; consumer lag

## M4 sim-engine / control-api

- Full scenario semantic validation and generator/timeline coverage
- Determinism integration test; `tests/e2e` compose job
- Ground-truth labels pipeline end-to-end

## M5 dashboard / stream-gateway

- API key manager UI; scenario editor with `:validate`
- uPlot live charts; anomaly feed; usage page
- OpenAPI-generated client; stream-gateway API-key via Redis cache
- SSE `Last-Event-ID` resume; per-tenant connection limits

## Infra

- Archive/replay: wire `S3_*` clients in stream-processor and sim-engine (config stubs exist)
- Optional: restore official MinIO images in compose when Docker Hub publishes them again; RustFS remains a valid S3-compatible dev target
