# stream-processor

Rust consumer for `telemetry.raw`: validate, dedupe, batch-write TimescaleDB, publish `telemetry.processed`.

M3 core pipeline is implemented; streaming **anomaly detectors** (EWMA, stuck-value, dropout) are the next increment on this service.

```bash
cd services/stream-processor
cargo test
cargo run
```

Env: `KAFKA_BROKERS`, `TIMESCALE_URL`, topic names (see `src/config.rs`).

S3-compatible archives (not implemented yet): `S3_ENDPOINT`, `S3_REGION` (default `us-east-1`), `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_FORCE_PATH_STYLE` (default `true`). See `src/s3_config.rs`.
