# sim-engine

Go scenario runtime: device telemetry and **traffic** profiles (`kind: traffic` via ingestion). Poisson arrivals, diurnal/spiky patterns, sessions/flows, `scale_traffic` timeline actions.

```bash
cd services/sim-engine
go test ./...
go run ./cmd/sim-engine
```

Replay archives (not implemented yet) will use `S3_*` env vars; see `internal/objectstore/config.go`.
