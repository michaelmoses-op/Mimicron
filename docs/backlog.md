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
