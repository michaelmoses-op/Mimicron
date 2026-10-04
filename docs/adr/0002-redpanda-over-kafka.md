# ADR 0002: Redpanda over managed Kafka

## Context

The pipeline needs Kafka-compatible topics with low local-dev friction.

## Decision

Run **Redpanda** in Docker Compose (Kafka API). Topic names and semantics match standard Kafka clients.

## Consequences

- Single container for dev; no ZooKeeper.
- Production can stay on Redpanda or migrate to managed Kafka with the same topic contract.
