use actix_web::{web, HttpResponse};
use chrono::NaiveDate;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::time::Duration;

use crate::config::Config;
use crate::errors::ApiError;

#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub service: String,
}

pub async fn health_check() -> HttpResponse {
    HttpResponse::Ok().json(HealthResponse {
        status: "healthy".to_string(),
        service: "rust-api".to_string(),
    })
}

#[derive(Debug, Deserialize)]
pub struct PriceQuery {
    pub start_date: Option<String>,
    pub end_date: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PriceAverage {
    pub date: String,
    pub average_price: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SuccessResponse {
    pub data: Vec<PriceAverage>,
}

#[derive(Debug, Deserialize)]
struct UpstreamErrorDetail {
    code: String,
    message: String,
}

#[derive(Debug, Deserialize)]
struct UpstreamErrorResponse {
    error: UpstreamErrorDetail,
}

fn parse_date(date_str: &str, param_name: &str) -> Result<NaiveDate, ApiError> {
    NaiveDate::parse_from_str(date_str, "%Y-%m-%d")
        .map_err(|_| ApiError::invalid_date_format(param_name))
}

fn validate_date_range(start: NaiveDate, end: NaiveDate) -> Result<(), ApiError> {
    if start > end {
        return Err(ApiError::invalid_date_range());
    }
    Ok(())
}

pub async fn get_price_averages(
    query: web::Query<PriceQuery>,
    config: web::Data<Config>,
) -> Result<HttpResponse, ApiError> {
    // Validate start_date
    let start_date_str = query
        .start_date
        .as_ref()
        .ok_or_else(|| ApiError::missing_parameter("start_date"))?;

    // Validate end_date
    let end_date_str = query
        .end_date
        .as_ref()
        .ok_or_else(|| ApiError::missing_parameter("end_date"))?;

    // Parse dates
    let start_date = parse_date(start_date_str, "start_date")?;
    let end_date = parse_date(end_date_str, "end_date")?;

    // Validate range
    validate_date_range(start_date, end_date)?;

    // Call Python API
    let client = Client::builder()
        .timeout(Duration::from_secs(config.python_api.timeout_seconds))
        .build()
        .map_err(|e| ApiError::internal_error(&e.to_string()))?;

    let url = format!(
        "{}/prices/average?start_date={}&end_date={}",
        config.python_api.url, start_date_str, end_date_str
    );

    let response = client
        .get(&url)
        .send()
        .await
        .map_err(|e| ApiError::upstream_error(&e.to_string()))?;

    let status = response.status();

    if status.is_success() {
        let body: SuccessResponse = response
            .json()
            .await
            .map_err(|e| ApiError::upstream_error(&format!("Invalid response format: {}", e)))?;

        Ok(HttpResponse::Ok().json(body))
    } else {
        // Try to parse error response from upstream
        let error_body = response.text().await.unwrap_or_default();

        if let Ok(upstream_error) = serde_json::from_str::<UpstreamErrorResponse>(&error_body) {
            Err(ApiError::upstream_error(&upstream_error.error.message))
        } else {
            Err(ApiError::upstream_error(&format!(
                "Upstream returned status {}",
                status
            )))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_valid_date() {
        let result = parse_date("2024-01-15", "start_date");
        assert!(result.is_ok());
        assert_eq!(
            result.unwrap(),
            NaiveDate::from_ymd_opt(2024, 1, 15).unwrap()
        );
    }

    #[test]
    fn test_parse_invalid_date_format() {
        let result = parse_date("15-01-2024", "start_date");
        assert!(result.is_err());
    }

    #[test]
    fn test_parse_invalid_date_value() {
        let result = parse_date("2024-13-45", "start_date");
        assert!(result.is_err());
    }

    #[test]
    fn test_validate_date_range_valid() {
        let start = NaiveDate::from_ymd_opt(2024, 1, 1).unwrap();
        let end = NaiveDate::from_ymd_opt(2024, 1, 31).unwrap();
        assert!(validate_date_range(start, end).is_ok());
    }

    #[test]
    fn test_validate_date_range_equal() {
        let date = NaiveDate::from_ymd_opt(2024, 1, 1).unwrap();
        assert!(validate_date_range(date, date).is_ok());
    }

    #[test]
    fn test_validate_date_range_invalid() {
        let start = NaiveDate::from_ymd_opt(2024, 1, 31).unwrap();
        let end = NaiveDate::from_ymd_opt(2024, 1, 1).unwrap();
        assert!(validate_date_range(start, end).is_err());
    }
}
