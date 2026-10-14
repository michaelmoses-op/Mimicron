# stream-gateway

Node / Express SSE fan-out for `telemetry.processed` and `anomalies.detected`.

## Auth

`GET /v1/stream` accepts:

- Short-lived **stream JWT** from `POST /v1/stream-tokens` (control-api; `read` scope or human JWT)
- **Access JWT** (`type: access`) from login/register
- **API key** (`mc_live_…` or `X-API-Key`) with `read` or `admin` scope — verified via Redis cache with fallback to control-api `POST /internal/v1/keys/verify`

Run tokens (`type: run`) are rejected for SSE.

## Config

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET` | Must match control-api |
| `REDIS_URL` | API key verify cache |
| `CONTROL_API_URL` | Internal verify base URL |
| `INTERNAL_API_SECRET` | `X-Internal-Secret` for verify |
| `KAFKA_BROKERS` | Redpanda |

```bash
cd services/stream-gateway
npm install
npm test
npm run dev
```
