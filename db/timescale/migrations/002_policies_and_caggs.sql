-- Compression, retention, continuous aggregates

ALTER TABLE measurements SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'tenant_id, device_id, metric',
  timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('measurements', INTERVAL '1 day', if_not_exists => TRUE);
SELECT add_retention_policy('measurements', INTERVAL '7 days', if_not_exists => TRUE);

CREATE MATERIALIZED VIEW IF NOT EXISTS measurements_1m
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 minute', time) AS bucket,
  tenant_id,
  device_id,
  metric,
  avg(value) AS avg_value,
  min(value) AS min_value,
  max(value) AS max_value,
  count(*) AS sample_count
FROM measurements
GROUP BY bucket, tenant_id, device_id, metric
WITH NO DATA;

SELECT add_continuous_aggregate_policy(
  'measurements_1m',
  start_offset => INTERVAL '1 hour',
  end_offset => INTERVAL '1 minute',
  schedule_interval => INTERVAL '1 minute',
  if_not_exists => TRUE
);

CREATE MATERIALIZED VIEW IF NOT EXISTS measurements_1h
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', bucket) AS bucket,
  tenant_id,
  device_id,
  metric,
  avg(avg_value) AS avg_value,
  min(min_value) AS min_value,
  max(max_value) AS max_value,
  sum(sample_count) AS sample_count
FROM measurements_1m
GROUP BY 1, tenant_id, device_id, metric
WITH NO DATA;

SELECT add_continuous_aggregate_policy(
  'measurements_1h',
  start_offset => INTERVAL '1 day',
  end_offset => INTERVAL '1 hour',
  schedule_interval => INTERVAL '1 hour',
  if_not_exists => TRUE
);
