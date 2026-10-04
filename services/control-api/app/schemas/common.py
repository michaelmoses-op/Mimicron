from __future__ import annotations

from pydantic import BaseModel


class QuotaOut(BaseModel):
    max_devices: int
    max_events_per_sec: int
    max_concurrent_runs: int
    max_run_duration_s: int
    retention_days: int
    max_api_rps: int
