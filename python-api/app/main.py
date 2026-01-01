from datetime import date
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from app.config import get_config
from app.errors import APIError, ErrorCode, api_error_handler
from app.tasks import compute_daily_averages_task

app = FastAPI(
    title="Quantfox Python API",
    version="1.0.0",
    description="Internal API for computing daily price averages using Celery tasks",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_exception_handler(APIError, api_error_handler)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify the service is running."""
    return {"status": "healthy", "service": "python-api"}


def validate_date(date_str: Optional[str], param_name: str) -> date:
    if date_str is None:
        raise APIError(
            code=ErrorCode.MISSING_PARAMETER,
            message=f"Missing required parameter: {param_name}",
            status_code=400,
        )

    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise APIError(
            code=ErrorCode.INVALID_DATE_FORMAT,
            message=f"Invalid date format for {param_name}. Expected ISO 8601 format (YYYY-MM-DD)",
            status_code=400,
        )


def validate_date_range(start: date, end: date) -> None:
    if start > end:
        raise APIError(
            code=ErrorCode.INVALID_DATE_RANGE,
            message="start_date must be before or equal to end_date",
            status_code=400,
        )


@app.get("/prices/average")
def get_price_averages(
    start_date: Optional[str] = Query(None, description="Start date in ISO 8601 format (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date in ISO 8601 format (YYYY-MM-DD)"),
) -> JSONResponse:
    # Validate parameters
    start = validate_date(start_date, "start_date")
    end = validate_date(end_date, "end_date")
    validate_date_range(start, end)

    try:
        # Execute Celery task and wait for result synchronously
        task = compute_daily_averages_task.delay(start.isoformat(), end.isoformat())
        result = task.get(timeout=60)

        return JSONResponse(
            status_code=200,
            content={"data": result},
        )
    except Exception as e:
        raise APIError(
            code=ErrorCode.TASK_ERROR,
            message=f"Failed to compute price averages: {str(e)}",
            status_code=500,
        )


if __name__ == "__main__":
    import uvicorn

    config = get_config()
    uvicorn.run(app, host=config.server.host, port=config.server.port)
