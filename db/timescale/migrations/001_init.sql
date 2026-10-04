-- Mimicron TimescaleDB schema (data plane)

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS measurements (
  time        timestamptz NOT NULL,
  ingest_time timestamptz NOT NULL,
  tenant_id   uuid        NOT NULL,
  run_id      uuid,
  device_id   text        NOT NULL,
  metric      text        NOT NULL,
  value       double precision NOT NULL,
  PRIMARY KEY (tenant_id, device_id, metric, time)
);

SELECT create_hypertable('measurements', 'time', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS measurements_tenant_run_time_idx
  ON measurements (tenant_id, run_id, time DESC);

CREATE TABLE IF NOT EXISTS devices (
  tenant_id   uuid NOT NULL,
  run_id      uuid,
  device_id   text NOT NULL,
  device_type text,
  tags        jsonb,
  first_seen  timestamptz,
  last_seen   timestamptz,
  PRIMARY KEY (tenant_id, device_id)
);

CREATE TABLE IF NOT EXISTS anomalies (
  time        timestamptz NOT NULL,
  tenant_id   uuid NOT NULL,
  run_id      uuid,
  device_id   text,
  metric      text,
  detector    text,
  severity    text,
  score       double precision,
  value       double precision,
  expected    double precision,
  details     jsonb
);

SELECT create_hypertable('anomalies', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS traffic_rollups_10s (
  time      timestamptz NOT NULL,
  tenant_id uuid NOT NULL,
  run_id    uuid,
  flow      text,
  region    text,
  requests  bigint,
  errors    bigint,
  p50_ms    real,
  p95_ms    real,
  p99_ms    real,
  bytes     bigint
);

SELECT create_hypertable('traffic_rollups_10s', 'time', if_not_exists => TRUE);
