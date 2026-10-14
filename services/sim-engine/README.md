# sim-engine

Go scenario runtime (device + traffic simulation). M0: health endpoints only.

```bash
cd services/sim-engine
go test ./...
go run ./cmd/sim-engine
```

Replay archives (not implemented yet) will use `S3_*` env vars; see `internal/objectstore/config.go`.
