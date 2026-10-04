use axum::{routing::get, Router};
use std::net::SocketAddr;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_| {
            "stream_processor=info,tower_http=info".into()
        }))
        .with(tracing_subscriber::fmt::layer().json())
        .init();

    let app = Router::new()
        .route("/healthz", get(|| async { r#"{"status":"ok"}"# }))
        .route("/readyz", get(|| async { r#"{"status":"ready"}"# }))
        .route(
            "/metrics",
            get(|| async { "# TYPE up gauge\nup 1\n" }),
        );

    let addr: SocketAddr = std::env::var("HTTP_ADDR")
        .unwrap_or_else(|_| "0.0.0.0:8091".into())
        .parse()
        .expect("HTTP_ADDR");

    tracing::info!(%addr, "stream-processor listening");
    let listener = tokio::net::TcpListener::bind(addr).await.expect("bind");
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await
        .expect("serve");
}

async fn shutdown_signal() {
    tokio::signal::ctrl_c()
        .await
        .expect("failed to install CTRL+C handler");
}

#[cfg(test)]
mod tests {
    use axum::body::Body;
    use axum::http::{Request, StatusCode};
    use tower::ServiceExt;

    #[tokio::test]
    async fn healthz_ok() {
        let app = axum::Router::new().route("/healthz", axum::routing::get(|| async { "ok" }));
        let response = app
            .oneshot(Request::builder().uri("/healthz").body(Body::empty()).unwrap())
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK);
    }
}
