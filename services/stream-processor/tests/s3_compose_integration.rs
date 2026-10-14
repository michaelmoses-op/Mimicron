//! Run against compose object storage:
//!   docker compose --profile infra up -d object-store object-store-init
//!   S3_ENDPOINT=http://127.0.0.1:9000 S3_ACCESS_KEY=... S3_SECRET_KEY=... cargo test -p stream-processor --test s3_compose_integration -- --ignored
use stream_processor::s3_config::S3Config;

#[test]
#[ignore = "requires S3-compatible object store (compose object-store)"]
fn compose_object_store_env_is_configured() {
    let cfg = S3Config::from_env();
    assert!(
        cfg.is_configured(),
        "set S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY"
    );
}
