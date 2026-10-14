use chrono::{DateTime, Duration, Timelike, Utc};
use serde_json::Value;
use std::collections::HashMap;
use uuid::Uuid;

use crate::envelope::Envelope;

#[derive(Clone, Hash, PartialEq, Eq)]
pub struct BucketKey {
    pub tenant_id: Uuid,
    pub run_id: Option<Uuid>,
    pub flow: String,
    pub region: String,
    pub bucket: DateTime<Utc>,
}

#[derive(Default)]
pub struct BucketStats {
    pub latencies_ms: Vec<f32>,
    pub errors: u64,
    pub bytes: u64,
}

pub struct TrafficRollups {
    pending: HashMap<BucketKey, BucketStats>,
}

impl TrafficRollups {
    pub fn new() -> Self {
        Self {
            pending: HashMap::new(),
        }
    }

    pub fn ingest(&mut self, env: &Envelope) {
        if env.kind != "traffic" {
            return;
        }
        let Ok(parsed) = DateTime::parse_from_rfc3339(&env.event_time) else {
            return;
        };
        let event_time = parsed.with_timezone(&Utc);
        let Ok(tenant_id) = Uuid::parse_str(&env.tenant_id) else {
            return;
        };
        let run_id = env
            .run_id
            .as_ref()
            .and_then(|s| Uuid::parse_str(s).ok());
        let Some(obj) = env.data.as_object() else {
            return;
        };
        let flow = field_str(obj, "flow").unwrap_or_else(|| "default".into());
        let region = field_str(obj, "region").unwrap_or_else(|| "default".into());
        let latency = field_f64(obj, "latency_ms").unwrap_or(0.0) as f32;
        let status = field_i64(obj, "status").unwrap_or(200);
        let bytes = field_i64(obj, "bytes").unwrap_or(0).max(0) as u64;
        let bucket = truncate_10s(event_time);
        let key = BucketKey {
            tenant_id,
            run_id,
            flow,
            region,
            bucket,
        };
        let stats = self.pending.entry(key.clone()).or_default();
        stats.latencies_ms.push(latency);
        if status >= 400 {
            stats.errors += 1;
        }
        stats.bytes += bytes;
    }

    /// Returns buckets whose window ended at least `grace` before `now`.
    pub fn drain_ready(&mut self, now: DateTime<Utc>, grace: Duration) -> Vec<(BucketKey, BucketStats)> {
        let cutoff = now - grace;
        let keys: Vec<BucketKey> = self
            .pending
            .keys()
            .filter(|k| {
                k.bucket + Duration::try_seconds(10).unwrap_or_default() <= cutoff
            })
            .cloned()
            .collect();
        keys.into_iter()
            .filter_map(|k| self.pending.remove(&k).map(|s| (k, s)))
            .collect()
    }
}

pub fn truncate_10s(t: DateTime<Utc>) -> DateTime<Utc> {
    let sec = t.second() - (t.second() % 10);
    t.with_second(sec)
        .and_then(|x| x.with_nanosecond(0))
        .unwrap_or(t)
}

pub fn percentile(sorted: &[f32], p: f32) -> f32 {
    if sorted.is_empty() {
        return 0.0;
    }
    if sorted.len() == 1 {
        return sorted[0];
    }
    let rank = p * (sorted.len() as f32 - 1.0);
    let lo = rank.floor() as usize;
    let hi = rank.ceil() as usize;
    if lo == hi {
        return sorted[lo];
    }
    let frac = rank - lo as f32;
    sorted[lo] + (sorted[hi] - sorted[lo]) * frac
}

fn field_str(obj: &serde_json::Map<String, Value>, key: &str) -> Option<String> {
    obj.get(key).and_then(|v| match v {
        Value::String(s) => Some(s.clone()),
        _ => None,
    })
}

fn field_f64(obj: &serde_json::Map<String, Value>, key: &str) -> Option<f64> {
    obj.get(key).and_then(|v| v.as_f64())
}

fn field_i64(obj: &serde_json::Map<String, Value>, key: &str) -> Option<i64> {
    obj.get(key).and_then(|v| v.as_i64())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn truncate_10s_aligns() {
        let t = DateTime::parse_from_rfc3339("2024-01-01T12:34:56Z")
            .unwrap()
            .with_timezone(&Utc);
        let b = truncate_10s(t);
        assert_eq!(b.second(), 50);
    }

    #[test]
    fn percentile_median() {
        let mut v = vec![10.0, 20.0, 30.0, 40.0];
        v.sort_by(|a, b| a.partial_cmp(b).unwrap());
        assert!((percentile(&v, 0.5) - 25.0).abs() < 0.01);
    }
}
