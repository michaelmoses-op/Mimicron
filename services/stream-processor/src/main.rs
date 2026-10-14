mod config;
mod consumer;
mod dedupe;
mod detect;
mod envelope;
mod rollups;
mod sink;

use axum::{routing::get, Router};
use sqlx::postgres::PgPoolOptions;
use std::net::SocketAddr;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_| {
            "stream_processor=info".into()
        }))
        .with(tracing_subscriber::fmt::layer().json())
        .init();

    let cfg = config::Config::from_env();
    let pool = PgPoolOptions::new()
        .max_connections(10)
        .connect(&cfg.database_url)
        .await?;
    let sink = sink::Sink::new(pool.clone());

    let http_addr: SocketAddr = cfg.http_addr.parse()?;
    let ready_pool = pool.clone();
    tokio::spawn(async move {
        let app = Router::new()
            .route("/healthz", get(|| async { r#"{"status":"ok"}"# }))
            .route(
                "/readyz",
                get(move || {
                    let pool = ready_pool.clone();
                    async move {
                        match sqlx::query("SELECT 1").execute(&pool).await {
                            Ok(_) => r#"{"status":"ready"}"#,
                            Err(_) => r#"{"status":"not_ready"}"#,
                        }
                    }
                }),
            )
            .route("/metrics", get(|| async { "# TYPE up gauge\nup 1\n" }));
        let listener = tokio::net::TcpListener::bind(http_addr).await.unwrap();
        axum::serve(listener, app).await.unwrap();
    });

    consumer::run(cfg, sink).await
}
