mod config;
mod errors;
mod handlers;

use actix_web::{web, App, HttpServer};
use tracing::info;
use tracing_subscriber::EnvFilter;

use config::Config;
use handlers::{get_price_averages, health_check};

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Load configuration
    let config = Config::from_env().expect("Failed to load configuration");

    // Initialize logging
    let filter = EnvFilter::try_new(&config.logging.level)
        .unwrap_or_else(|_| EnvFilter::new("info"));

    tracing_subscriber::fmt()
        .with_env_filter(filter)
        .init();

    let bind_address = format!("{}:{}", config.server.host, config.server.port);
    info!("Starting Rust API server on {}", bind_address);

    let config_data = web::Data::new(config);

    HttpServer::new(move || {
        App::new()
            .app_data(config_data.clone())
            .route("/health", web::get().to(health_check))
            .route("/prices/average", web::get().to(get_price_averages))
    })
    .bind(&bind_address)?
    .run()
    .await
}
