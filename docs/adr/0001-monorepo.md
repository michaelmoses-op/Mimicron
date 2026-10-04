# ADR 0001: Monorepo

## Context

Mimicron is one product with many services, shared contracts, and cross-service e2e tests. Split repos add coordination cost without independent release cycles in early milestones.

## Decision

Use a single monorepo with `services/`, `contracts/`, `docs/`, and shared `docker-compose.yml` / Makefile.

## Consequences

- Path-filtered CI keeps feedback fast.
- Contract changes and service changes land in one PR.
- Clone size grows; acceptable for portfolio scale.
