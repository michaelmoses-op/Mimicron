# ingestion-gateway

Go public ingestion API (`POST /v1/ingest`).

## Run

```bash
cd services/ingestion-gateway
go run ./cmd/ingestion-gateway
```

Env: `REDIS_URL`, `KAFKA_BROKERS`, `CONTROL_API_URL`, `INTERNAL_API_SECRET`, `JWT_SECRET`.

## Test

```bash
go test ./...
```

See [tests/e2e/INGEST.md](../../tests/e2e/INGEST.md) for full pipeline smoke test.
