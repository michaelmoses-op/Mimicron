# ADR 0005: Narrow measurement schema

## Context

Device metrics vary by scenario; wide tables or per-metric columns do not scale for a generic simulator.

## Decision

Store telemetry in a **narrow** `measurements(time, tenant_id, device_id, metric, value, ...)` hypertable with idempotent primary key `(tenant_id, device_id, metric, time)`.

## Consequences

- Any scenario metric fits without migrations.
- Queries filter by `metric`; continuous aggregates roll up per metric.
