# stream-processor

Rust consumer for `telemetry.raw`: validate, dedupe, batch-write TimescaleDB, publish `telemetry.processed`.

M3 core pipeline is implemented; streaming **anomaly detectors** (EWMA, stuck-value, dropout) are the next increment on this service.

```bash
cd services/stream-processor
cargo test
cargo run
```

Env: `KAFKA_BROKERS`, `TIMESCALE_URL`, topic names (see `src/config.rs`).
