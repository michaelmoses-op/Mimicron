use std::env;

#[derive(Clone, Debug)]
pub struct Config {
    pub kafka_brokers: String,
    pub raw_topic: String,
    pub processed_topic: String,
    pub anomalies_topic: String,
    pub dlq_topic: String,
    pub group_id: String,
    pub database_url: String,
    pub batch_size: usize,
    pub http_addr: String,
}

impl Config {
    pub fn from_env() -> Self {
        Self {
            kafka_brokers: env_var("KAFKA_BROKERS", "localhost:19092"),
            raw_topic: env_var("TELEMETRY_RAW_TOPIC", "telemetry.raw"),
            processed_topic: env_var("TELEMETRY_PROCESSED_TOPIC", "telemetry.processed"),
            anomalies_topic: env_var("ANOMALIES_TOPIC", "anomalies.detected"),
            dlq_topic: env_var("TELEMETRY_DLQ_TOPIC", "telemetry.dlq"),
            group_id: env_var("KAFKA_GROUP_ID", "stream-processor"),
            database_url: env_var(
                "TIMESCALE_URL",
                "postgres://mimicron:mimicron_dev@localhost:5433/mimicron_ts",
            ),
            batch_size: env_var("BATCH_SIZE", "200").parse().unwrap_or(200),
            http_addr: env_var("HTTP_ADDR", "0.0.0.0:8091"),
        }
    }
}

fn env_var(key: &str, default: &str) -> String {
    env::var(key).unwrap_or_else(|_| default.to_string())
}
