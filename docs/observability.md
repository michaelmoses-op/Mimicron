# Observability

## Stack (local / VM)

| Component | Port | Role |
|-----------|------|------|
| Prometheus | 9090 | Scrapes `/metrics` on app services |
| Grafana | 3001 | Dashboards (`admin` / see `GRAFANA_PASSWORD`) |
| Jaeger UI | 16686 | Trace visualization |
| OTel Collector | 4317 gRPC, 4318 HTTP | Receives OTLP from control-api |

Enable with compose profile **`all`** (includes observability) or **`observability`** alongside **`services`**.

```bash
# Traces from control-api (optional)
export OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
make up
```

## Metrics

- **control-api:** `prometheus_client` default metrics + `/metrics`
- **ingestion-gateway:** `http_requests_total`, `http_request_duration_seconds` (RED-oriented)
- Other services: minimal `up` gauge until expanded (see `docs/backlog.md`)

Prometheus config: `infra/observability/prometheus/prometheus.yml`

Grafana provisioning: `infra/observability/grafana/provisioning/`

## Tracing

- **HTTP:** W3C `traceparent` on control-api (OTel SDK when OTLP endpoint set).
- **Kafka:** ingestion-gateway copies `traceparent` to record headers for downstream consumers (stream-processor wiring is backlog).

## Logs

JSON logs to stdout; include `request_id` and `trace_id` (control-api) for correlation.
