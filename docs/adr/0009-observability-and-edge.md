# ADR 0009: Observability stack and Caddy edge

## Context

M8 requires metrics, traces, dashboards, and a single-VM deploy story without binding to a cloud vendor load balancer.

## Decision

- **Metrics:** Prometheus scrapes service `/metrics`; Grafana provisioned from `infra/observability/`.
- **Traces:** OTel Collector + Jaeger; control-api exports OTLP when `OTEL_EXPORTER_OTLP_ENDPOINT` is set; ingestion-gateway propagates `traceparent` on Kafka headers.
- **Edge:** Caddy in `docker-compose.prod.yml` terminates TLS and routes `/api`, `/ingest`, `/stream`, dashboard, and static `/status`.

## Consequences

- **Pros:** One Compose file runs locally and on a VM; aligns with cloud-neutral ADR 0007.
- **Cons:** Not HA; full OTel instrumentation not yet in every service; status page is static until blackbox checks land in backlog.
