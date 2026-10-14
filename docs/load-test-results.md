# Load test results

Target (from AGENTS.md): ingestion gateway **~5,000 events/s** sustained on a small VM, **p99 ack &lt; 50 ms** (verify on your hardware).

## How to reproduce

```bash
make up
pip install httpx
API_KEY=$(python scripts/ci_provision_ingest_key.py http://localhost:8000)
INGEST_URL=http://localhost:8081/v1/ingest API_KEY=$API_KEY k6 run tests/load/ingest_smoke.js
```

For heavier runs, increase `vus` / `duration` in `tests/load/ingest_smoke.js` or add a dedicated script under `tests/load/`.

## Published run (fill in after you measure)

| Date | Host | k6 config | Throughput | p99 ack (ms) | Notes |
|------|------|-----------|------------|--------------|-------|
| _TBD_ | e.g. 4 vCPU / 8 GB VM | 2 VUs, 10s smoke | — | — | CI smoke only until manual run |

CI runs the **smoke** thresholds (`rate<0.05` errors, `p(99)<500ms`) — not the 5k/s SLO.
