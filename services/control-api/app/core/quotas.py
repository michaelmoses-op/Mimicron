from __future__ import annotations

from dataclasses import dataclass

from app.db.models import Quota


@dataclass(frozen=True)
class QuotaValues:
    max_devices: int
    max_events_per_sec: int
    max_concurrent_runs: int
    max_run_duration_s: int
    retention_days: int
    max_api_rps: int

    def to_dict(self) -> dict[str, int]:
        return {
            "max_devices": self.max_devices,
            "max_events_per_sec": self.max_events_per_sec,
            "max_concurrent_runs": self.max_concurrent_runs,
            "max_run_duration_s": self.max_run_duration_s,
            "retention_days": self.retention_days,
            "max_api_rps": self.max_api_rps,
        }


TIER_DEFAULTS: dict[str, QuotaValues] = {
    "free": QuotaValues(
        max_devices=500,
        max_events_per_sec=500,
        max_concurrent_runs=2,
        max_run_duration_s=7200,
        retention_days=7,
        max_api_rps=30,
    ),
    "pro": QuotaValues(
        max_devices=5000,
        max_events_per_sec=5000,
        max_concurrent_runs=10,
        max_run_duration_s=86400,
        retention_days=30,
        max_api_rps=120,
    ),
}


def quota_for_tier(tier: str) -> QuotaValues:
    return TIER_DEFAULTS.get(tier, TIER_DEFAULTS["free"])


def quota_from_model(q: Quota) -> QuotaValues:
    return QuotaValues(
        max_devices=q.max_devices,
        max_events_per_sec=q.max_events_per_sec,
        max_concurrent_runs=q.max_concurrent_runs,
        max_run_duration_s=q.max_run_duration_s,
        retention_days=q.retention_days,
        max_api_rps=q.max_api_rps,
    )
