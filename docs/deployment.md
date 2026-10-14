# Deployment (single VM)

First production target: **Docker Compose on one Linux VM** (Hetzner, DigitalOcean, Linode, etc.). No managed AWS services in the default path ([ADR 0007](adr/0007-cloud-neutral-deployment.md)).

## Layout

| Path | Purpose |
|------|---------|
| `docker-compose.yml` | Full dev/staging stack |
| `docker-compose.prod.yml` | Caddy TLS + path routing overlay |
| `infra/deploy/Caddyfile` | `/api`, `/ingest`, `/stream`, dashboard, `/status` |
| `infra/terraform/providers/generic-vm/` | Placeholder VM + cloud-init |
| `.env` | Secrets and public URLs (never commit) |

## Local production-like smoke

```bash
cp .env.example .env
# Set PUBLIC_DOMAIN=localhost for HTTP-only Caddy, or your DNS name for TLS.
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile all up -d --build
```

Routes (via Caddy on port 80/443):

- `https://<domain>/` — dashboard  
- `https://<domain>/api/` — control-api (strip prefix in Caddy → upstream root)  
- `https://<domain>/ingest/v1/ingest` — ingestion gateway  
- `https://<domain>/stream/` — SSE gateway  
- `https://<domain>/status/` — static status page  

**Note:** Dashboard build args (`VITE_API_URL`, `VITE_STREAM_URL`) must match the public URLs browsers will use.

## VM bootstrap (manual)

1. Ubuntu 22.04+ VM, open ports 80/443 (and 22 for SSH).
2. Install Docker Engine + Compose plugin.
3. Clone repo, copy `.env`, set strong `JWT_SECRET`, `INTERNAL_API_SECRET`, DB passwords.
4. `docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile all up -d --build`
5. Optional: enable observability env `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318` when using the `all` profile.

## Terraform

See `infra/terraform/providers/generic-vm/README.md`. Provider-specific modules (Hetzner, DO, …) stay under `infra/terraform/providers/<name>/`.

## External developers

They need **your public HTTPS URLs** and an **API key** from control-api — not GHCR or CI settings. See [architecture.md](architecture.md) auth and data-plane sections.
