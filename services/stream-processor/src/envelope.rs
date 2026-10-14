use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Envelope {
    pub schema_version: i32,
    pub event_id: String,
    pub kind: String,
    pub tenant_id: String,
    pub run_id: Option<String>,
    pub device_id: String,
    pub device_type: Option<String>,
    pub event_time: String,
    pub ingest_time: String,
    pub seq: Option<i64>,
    pub tags: Option<Value>,
    pub data: Value,
}
