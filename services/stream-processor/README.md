# stream-processor

Rust consumer for `telemetry.raw`: validate, dedupe, batch-write TimescaleDB, publish `telemetry.processed`.

M3 core pipeline is implemented; streaming **anomaly detectors** (EWMA, stuck-value, dropout) are the next increment on this service.

```bash
cd services/stream-processor
cargo test
cargo run
```

Env: `KAFKA_BROKERS`, `TIMESCALE_URL`, topic names (see `src/config.rs`).

Consumes `kind: traffic` events and writes **10s rollups** to `traffic_rollups_10s` (flow/region, RPS, errors, p50/p95/p99).

S3-compatible archives (not implemented yet): `S3_ENDPOINT`, `S3_REGION` (default `us-east-1`), `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_FORCE_PATH_STYLE` (default `true`). See `src/s3_config.rs`.
