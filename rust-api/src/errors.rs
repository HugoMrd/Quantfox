use actix_web::{http::StatusCode, HttpResponse, ResponseError};
use serde::Serialize;
use std::fmt;

#[derive(Debug, Clone, Serialize)]
pub enum ErrorCode {
    #[serde(rename = "MISSING_PARAMETER")]
    MissingParameter,
    #[serde(rename = "INVALID_DATE_FORMAT")]
    InvalidDateFormat,
    #[serde(rename = "INVALID_DATE_RANGE")]
    InvalidDateRange,
    #[serde(rename = "UPSTREAM_ERROR")]
    UpstreamError,
    #[serde(rename = "INTERNAL_ERROR")]
    InternalError,
}

#[derive(Debug, Serialize)]
struct ErrorDetail {
    code: ErrorCode,
    message: String,
}

#[derive(Debug, Serialize)]
struct ErrorResponse {
    error: ErrorDetail,
}

#[derive(Debug)]
pub struct ApiError {
    pub code: ErrorCode,
    pub message: String,
    pub status_code: StatusCode,
}

impl ApiError {
    pub fn missing_parameter(param: &str) -> Self {
        Self {
            code: ErrorCode::MissingParameter,
            message: format!("Missing required parameter: {}", param),
            status_code: StatusCode::BAD_REQUEST,
        }
    }

    pub fn invalid_date_format(param: &str) -> Self {
        Self {
            code: ErrorCode::InvalidDateFormat,
            message: format!(
                "Invalid date format for {}. Expected ISO 8601 format (YYYY-MM-DD)",
                param
            ),
            status_code: StatusCode::BAD_REQUEST,
        }
    }

    pub fn invalid_date_range() -> Self {
        Self {
            code: ErrorCode::InvalidDateRange,
            message: "start_date must be before or equal to end_date".to_string(),
            status_code: StatusCode::BAD_REQUEST,
        }
    }

    pub fn upstream_error(msg: &str) -> Self {
        Self {
            code: ErrorCode::UpstreamError,
            message: format!("Upstream service error: {}", msg),
            status_code: StatusCode::BAD_GATEWAY,
        }
    }

    pub fn internal_error(msg: &str) -> Self {
        Self {
            code: ErrorCode::InternalError,
            message: format!("Internal server error: {}", msg),
            status_code: StatusCode::INTERNAL_SERVER_ERROR,
        }
    }
}

impl fmt::Display for ApiError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.message)
    }
}

impl ResponseError for ApiError {
    fn status_code(&self) -> StatusCode {
        self.status_code
    }

    fn error_response(&self) -> HttpResponse {
        let response = ErrorResponse {
            error: ErrorDetail {
                code: self.code.clone(),
                message: self.message.clone(),
            },
        };

        HttpResponse::build(self.status_code).json(response)
    }
}
