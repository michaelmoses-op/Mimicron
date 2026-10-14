use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use sqlx::{PgPool, Row};
use uuid::Uuid;

use crate::detect::AnomalyRecord;
use crate::envelope::Envelope;
use crate::rollups::{percentile, BucketKey, BucketStats};

pub struct Sink {
    pool: PgPool,
}

impl Sink {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    pub async fn write_batch(&self, events: &[Envelope]) -> Result<u64> {
        let mut written = 0u64;
        let mut tx = self.pool.begin().await?;
        for env in events {
            if env.kind != "telemetry" {
                continue;
            }
            let event_time: DateTime<Utc> =
                DateTime::parse_from_rfc3339(&env.event_time).map(|d| d.with_timezone(&Utc))?;
            let ingest_time: DateTime<Utc> =
                DateTime::parse_from_rfc3339(&env.ingest_time).map(|d| d.with_timezone(&Utc))?;
            let tenant_id = Uuid::parse_str(&env.tenant_id)?;
            let run_id = env
                .run_id
                .as_ref()
                .map(|s| Uuid::parse_str(s))
                .transpose()?;
            let obj = env
                .data
                .as_object()
                .context("telemetry data must be object")?;
            for (metric, value) in obj {
                let v = value.as_f64().context("metric must be number")?;
                let res = sqlx::query(
                    r#"
                    INSERT INTO measurements (time, ingest_time, tenant_id, run_id, device_id, metric, value)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT DO NOTHING
                    "#,
                )
                .bind(event_time)
                .bind(ingest_time)
                .bind(tenant_id)
                .bind(run_id)
                .bind(&env.device_id)
                .bind(metric)
                .bind(v)
                .execute(&mut *tx)
                .await?;
                written += res.rows_affected();
            }
            let device_type = env.device_type.as_deref().unwrap_or("");
            let tags = env.tags.clone().unwrap_or(serde_json::json!({}));
            sqlx::query(
                r#"
                INSERT INTO devices (tenant_id, run_id, device_id, device_type, tags, first_seen, last_seen)
                VALUES ($1, $2, $3, $4, $5, $6, $6)
                ON CONFLICT (tenant_id, device_id) DO UPDATE SET
                  last_seen = EXCLUDED.last_seen,
                  device_type = COALESCE(NULLIF(EXCLUDED.device_type, ''), devices.device_type),
                  tags = EXCLUDED.tags,
                  run_id = COALESCE(EXCLUDED.run_id, devices.run_id)
                "#,
            )
            .bind(tenant_id)
            .bind(run_id)
            .bind(&env.device_id)
            .bind(device_type)
            .bind(tags)
            .bind(ingest_time)
            .execute(&mut *tx)
            .await?;
        }
        tx.commit().await?;
        Ok(written)
    }

    pub async fn upsert_traffic_rollups(&self, buckets: &[(BucketKey, BucketStats)]) -> Result<()> {
        if buckets.is_empty() {
            return Ok(());
        }
        let mut tx = self.pool.begin().await?;
        for (key, stats) in buckets {
            let mut lat = stats.latencies_ms.clone();
            lat.sort_by(|a, b| a.partial_cmp(b).unwrap());
            let requests = lat.len() as i64;
            let p50 = percentile(&lat, 0.5);
            let p95 = percentile(&lat, 0.95);
            let p99 = percentile(&lat, 0.99);
            sqlx::query(
                r#"
                INSERT INTO traffic_rollups_10s
                  (time, tenant_id, run_id, flow, region, requests, errors, p50_ms, p95_ms, p99_ms, bytes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (tenant_id, run_id, flow, region, time) DO UPDATE SET
                  requests = traffic_rollups_10s.requests + EXCLUDED.requests,
                  errors = traffic_rollups_10s.errors + EXCLUDED.errors,
                  bytes = traffic_rollups_10s.bytes + EXCLUDED.bytes,
                  p50_ms = EXCLUDED.p50_ms,
                  p95_ms = EXCLUDED.p95_ms,
                  p99_ms = EXCLUDED.p99_ms
                "#,
            )
            .bind(key.bucket)
            .bind(key.tenant_id)
            .bind(key.run_id)
            .bind(&key.flow)
            .bind(&key.region)
            .bind(requests)
            .bind(stats.errors as i64)
            .bind(p50)
            .bind(p95)
            .bind(p99)
            .bind(stats.bytes as i64)
            .execute(&mut *tx)
            .await?;
        }
        tx.commit().await?;
        Ok(())
    }

    pub async fn insert_anomalies(&self, rows: &[AnomalyRecord]) -> Result<()> {
        if rows.is_empty() {
            return Ok(());
        }
        let mut tx = self.pool.begin().await?;
        for row in rows {
            sqlx::query(
                r#"
                INSERT INTO anomalies
                  (time, tenant_id, run_id, device_id, metric, detector, severity, score, value, expected)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                "#,
            )
            .bind(row.time)
            .bind(row.tenant_id)
            .bind(row.run_id)
            .bind(&row.device_id)
            .bind(&row.metric)
            .bind(&row.detector)
            .bind(&row.severity)
            .bind(row.score)
            .bind(row.value)
            .bind(row.expected)
            .execute(&mut *tx)
            .await?;
        }
        tx.commit().await?;
        Ok(())
    }

    pub async fn ping(&self) -> Result<()> {
        let row = sqlx::query("SELECT 1 AS ok").fetch_one(&self.pool).await?;
        let _: i32 = row.get("ok");
        Ok(())
    }
}
