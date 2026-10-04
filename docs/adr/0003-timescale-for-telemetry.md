# ADR 0003: TimescaleDB for telemetry

## Context

Telemetry is append-heavy time series with tenant isolation, retention, compression, and SQL aggregations for the query API.

## Decision

Use a **separate TimescaleDB** instance for the data plane; PostgreSQL holds control-plane metadata only.

## Consequences

- Hypertables, compression, continuous aggregates, and retention policies fit the access model.
- control-api uses a read-only role and always filters by `tenant_id`.
