# ADR 0006: No Cassandra

## Context

Some IoT platforms use Cassandra for ingestion scale. Mimicron targets a portfolio-grade but operable stack on a single VM first.

## Decision

**Do not** introduce Cassandra. TimescaleDB is the telemetry store; evaluate ClickHouse later via ADR if needed.

## Consequences

- Simpler ops and fewer moving parts in M0–M8.
- Peak ingestion targets must fit Timescale + stream-processor batching (validated in load tests).
