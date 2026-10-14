use chrono::{DateTime, Utc};
use lru::LruCache;
use std::num::NonZeroUsize;
use uuid::Uuid;

use crate::envelope::Envelope;

#[derive(Debug, Clone, serde::Serialize)]
pub struct AnomalyRecord {
    pub time: DateTime<Utc>,
    pub tenant_id: Uuid,
    pub run_id: Option<Uuid>,
    pub device_id: String,
    pub metric: String,
    pub detector: String,
    pub severity: String,
    pub score: f64,
    pub value: f64,
    pub expected: Option<f64>,
}

#[derive(Debug, Clone, Hash, PartialEq, Eq)]
struct SeriesKey {
    tenant_id: Uuid,
    device_id: String,
    metric: String,
}

#[derive(Default)]
struct SeriesState {
    ewma: Option<f64>,
    ewma_var: f64,
    stuck_value: Option<f64>,
    stuck_count: u32,
    last_time: Option<DateTime<Utc>>,
    median_interval_ms: f64,
}

pub struct DetectionPipeline {
    states: LruCache<SeriesKey, SeriesState>,
    alpha: f64,
    z_threshold: f64,
    stuck_n: u32,
    dropout_factor: f64,
}

impl DetectionPipeline {
    pub fn new(capacity: usize) -> Self {
        Self {
            states: LruCache::new(NonZeroUsize::new(capacity.max(1)).unwrap()),
            alpha: 0.2,
            z_threshold: 3.0,
            stuck_n: 5,
            dropout_factor: 3.0,
        }
    }

    pub fn ingest(&mut self, env: &Envelope) -> Vec<AnomalyRecord> {
        if env.kind != "telemetry" {
            return vec![];
        }
        let Ok(tenant_id) = Uuid::parse_str(&env.tenant_id) else {
            return vec![];
        };
        let Ok(event_time) = DateTime::parse_from_rfc3339(&env.event_time)
            .map(|d| d.with_timezone(&Utc))
        else {
            return vec![];
        };
        let run_id = env
            .run_id
            .as_ref()
            .and_then(|s| Uuid::parse_str(s).ok());
        let Some(obj) = env.data.as_object() else {
            return vec![];
        };

        let mut out = Vec::new();
        for (metric, value) in obj {
            let Some(v) = value.as_f64() else {
                continue;
            };
            let key = SeriesKey {
                tenant_id,
                device_id: env.device_id.clone(),
                metric: metric.clone(),
            };
            let state = self.states.get_or_insert_mut(key.clone(), SeriesState::default);

            if let Some(prev) = state.last_time {
                let gap_ms = (event_time - prev).num_milliseconds().max(0) as f64;
                if gap_ms > 0.0 {
                    state.median_interval_ms = if state.median_interval_ms <= 0.0 {
                        gap_ms
                    } else {
                        state.median_interval_ms * 0.9 + gap_ms * 0.1
                    };
                    let threshold = state.median_interval_ms * self.dropout_factor;
                    if gap_ms > threshold && state.median_interval_ms > 0.0 {
                        out.push(AnomalyRecord {
                            time: event_time,
                            tenant_id,
                            run_id,
                            device_id: env.device_id.clone(),
                            metric: metric.clone(),
                            detector: "dropout".into(),
                            severity: "medium".into(),
                            score: gap_ms / threshold,
                            value: v,
                            expected: Some(state.median_interval_ms),
                        });
                    }
                }
            }
            state.last_time = Some(event_time);

            if state.stuck_value == Some(v) {
                state.stuck_count += 1;
            } else {
                state.stuck_value = Some(v);
                state.stuck_count = 1;
            }
            if state.stuck_count >= self.stuck_n {
                out.push(AnomalyRecord {
                    time: event_time,
                    tenant_id,
                    run_id,
                    device_id: env.device_id.clone(),
                    metric: metric.clone(),
                    detector: "stuck_value".into(),
                    severity: "low".into(),
                    score: state.stuck_count as f64,
                    value: v,
                    expected: None,
                });
                state.stuck_count = 0;
            }

            let mean = match state.ewma {
                None => {
                    state.ewma = Some(v);
                    state.ewma_var = 0.0;
                    continue;
                }
                Some(m) => {
                    let next = self.alpha * v + (1.0 - self.alpha) * m;
                    let diff = v - m;
                    state.ewma_var =
                        self.alpha * diff * diff + (1.0 - self.alpha) * state.ewma_var;
                    state.ewma = Some(next);
                    next
                }
            };
            let std = state.ewma_var.sqrt();
            if std > f64::EPSILON {
                let z = (v - mean).abs() / std;
                if z >= self.z_threshold {
                    let severity = if z >= self.z_threshold * 1.5 {
                        "high"
                    } else {
                        "medium"
                    };
                    out.push(AnomalyRecord {
                        time: event_time,
                        tenant_id,
                        run_id,
                        device_id: env.device_id.clone(),
                        metric: metric.clone(),
                        detector: "ewma_zscore".into(),
                        severity: severity.into(),
                        score: z,
                        value: v,
                        expected: Some(mean),
                    });
                }
            }
        }
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn telemetry(value: f64, t: &str) -> Envelope {
        Envelope {
            schema_version: 1,
            event_id: uuid::Uuid::new_v4().to_string(),
            kind: "telemetry".into(),
            tenant_id: uuid::Uuid::new_v4().to_string(),
            run_id: None,
            device_id: "d1".into(),
            device_type: None,
            event_time: t.into(),
            ingest_time: t.into(),
            seq: Some(1),
            tags: None,
            data: json!({ "temp": value }),
        }
    }

    #[test]
    fn stuck_value_fires_after_n_identical() {
        let mut p = DetectionPipeline::new(100);
        let mut hits = 0;
        for i in 0..6 {
            let t = format!("2024-01-01T00:00:{i:02}Z");
            hits += p.ingest(&telemetry(42.0, &t)).len();
        }
        assert!(hits >= 1);
    }

    #[test]
    fn ewma_spike_detected() {
        let mut p = DetectionPipeline::new(100);
        for i in 0..20 {
            let t = format!("2024-01-01T00:00:{i:02}Z");
            let _ = p.ingest(&telemetry(20.0, &t));
        }
        let spike = p.ingest(&telemetry(200.0, "2024-01-01T00:00:20Z"));
        assert!(spike.iter().any(|a| a.detector == "ewma_zscore"));
    }
}
