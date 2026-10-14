//! S3-compatible object storage settings (archives/replay — not wired yet).
use std::env;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct S3Config {
    pub endpoint: String,
    pub region: String,
    pub bucket: String,
    pub access_key: String,
    pub secret_key: String,
    pub force_path_style: bool,
}

impl S3Config {
    pub fn from_env() -> Self {
        Self {
            endpoint: env_var("S3_ENDPOINT", ""),
            region: env_var("S3_REGION", "us-east-1"),
            bucket: env_var("S3_BUCKET", ""),
            access_key: env_var("S3_ACCESS_KEY", ""),
            secret_key: env_var("S3_SECRET_KEY", ""),
            force_path_style: env_bool("S3_FORCE_PATH_STYLE", true),
        }
    }

    /// True when enough settings exist to open a client (archive path not implemented yet).
    pub fn is_configured(&self) -> bool {
        !self.endpoint.is_empty()
            && !self.bucket.is_empty()
            && !self.access_key.is_empty()
            && !self.secret_key.is_empty()
    }
}

fn env_var(key: &str, default: &str) -> String {
    env::var(key).unwrap_or_else(|_| default.to_string())
}

fn env_bool(key: &str, default: bool) -> bool {
    match env::var(key) {
        Ok(v) => matches!(v.to_ascii_lowercase().as_str(), "1" | "true" | "yes" | "on"),
        Err(_) => default,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{Mutex, OnceLock};

    static ENV_LOCK: OnceLock<Mutex<()>> = OnceLock::new();

    fn env_lock() -> std::sync::MutexGuard<'static, ()> {
        ENV_LOCK.get_or_init(|| Mutex::new(())).lock().unwrap()
    }

    #[test]
    fn defaults_region_and_path_style() {
        let _guard = env_lock();
        for key in [
            "S3_ENDPOINT",
            "S3_REGION",
            "S3_BUCKET",
            "S3_ACCESS_KEY",
            "S3_SECRET_KEY",
            "S3_FORCE_PATH_STYLE",
        ] {
            env::remove_var(key);
        }
        let cfg = S3Config::from_env();
        assert_eq!(cfg.region, "us-east-1");
        assert!(cfg.force_path_style);
        assert!(!cfg.is_configured());
    }

    #[test]
    fn reads_standard_env_vars() {
        let _guard = env_lock();
        env::set_var("S3_ENDPOINT", "http://127.0.0.1:9000");
        env::set_var("S3_REGION", "garage");
        env::set_var("S3_BUCKET", "mimicron-archives");
        env::set_var("S3_ACCESS_KEY", "key");
        env::set_var("S3_SECRET_KEY", "secret");
        env::set_var("S3_FORCE_PATH_STYLE", "false");
        let cfg = S3Config::from_env();
        assert!(cfg.is_configured());
        assert_eq!(cfg.endpoint, "http://127.0.0.1:9000");
        assert_eq!(cfg.region, "garage");
        assert!(!cfg.force_path_style);
    }
}
