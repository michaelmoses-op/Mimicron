# ADR 0004: Rust only for stream-processor

## Context

The hot path (consume, validate, dedupe, batch write, detectors) needs predictable latency and memory on long runs.

## Decision

Implement **stream-processor** in Rust (tokio, rdkafka, sqlx). No other Rust services.

## Consequences

- One Rust toolchain and Dockerfile to maintain in CI.
- Go/Python/TS remain the default for other services.
