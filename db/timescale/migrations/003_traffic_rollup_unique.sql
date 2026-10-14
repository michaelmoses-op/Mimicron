-- Idempotent upserts for 10s traffic rollups (stream-processor).
CREATE UNIQUE INDEX IF NOT EXISTS traffic_rollups_10s_tenant_run_flow_region_time_idx
  ON traffic_rollups_10s (tenant_id, run_id, flow, region, time);
