# Ingest pipeline smoke test (M2 + M3)

Requires `make up` with Docker.

## 1. Register and create an ingest key

```bash
BASE=http://localhost:8000
REG=$(curl -s -X POST "$BASE/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"ingest-test@example.com","password":"password1234"}')
TOKEN=$(echo "$REG" | jq -r .access_token)
KEY=$(curl -s -X POST "$BASE/v1/api-keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"ingest","scopes":["ingest"]}')
SECRET=$(echo "$KEY" | jq -r .secret)
```

## 2. POST telemetry

```bash
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8081/v1/ingest \
  -H "X-API-Key: $SECRET" \
  -H "Content-Type: application/json" \
  -d "{\"events\":[{\"device_id\":\"manual-1\",\"event_time\":\"$NOW\",\"data\":{\"temperature_c\":22.1}}]}"
```

Expect `202`.

## 3. Verify Timescale row (after ~2s)

```bash
docker compose exec timescale psql -U mimicron -d mimicron_ts -c \
  "SELECT device_id, metric, value FROM measurements ORDER BY ingest_time DESC LIMIT 5;"
```

## 4. k6 (optional)

```bash
API_KEY=$SECRET k6 run tests/load/ingest_smoke.js
```
