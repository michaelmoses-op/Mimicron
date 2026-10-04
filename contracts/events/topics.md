# Redpanda topics (Kafka API)

Delivery: **at-least-once**. Consumers commit offsets only after a successful sink flush.

## Headers (all topics)

| Header | Description |
|--------|-------------|
| `tenant_id` | UUID string |
| `schema_version` | Event/schema version (integer as string) |
| `traceparent` | W3C trace context |

`telemetry.dlq` messages also carry a **`reason`** header (validation, dedupe, sink error, etc.).

## Topics

| Topic | Key | Partitions (dev) | Retention (dev) | Producer | Consumer(s) |
|-------|-----|------------------|-----------------|----------|-------------|
| `sim.commands` | `run_id` | 3 | 7d | control-api | sim-engine |
| `sim.events` | `run_id` | 3 | 7d | sim-engine | control-api |
| `telemetry.raw` | `{tenant_id}:{device_id}` | 12 | 24h | ingestion-gateway | stream-processor |
| `telemetry.processed` | `{tenant_id}:{device_id}` | 12 | 24h | stream-processor | stream-gateway |
| `anomalies.detected` | `{tenant_id}:{device_id}` | 6 | 7d | stream-processor | stream-gateway |
| `telemetry.dlq` | `{tenant_id}` | 3 | 7d | stream-processor | ops / replay (later) |

## Payload

- **sim.commands / sim.events:** JSON command/status envelopes (defined in service code; contract tests in later milestones).
- **telemetry.*** / **anomalies.detected:** JSON event envelope per [`envelope.schema.json`](./envelope.schema.json) (processed events may add normalized fields in a later contract revision).
