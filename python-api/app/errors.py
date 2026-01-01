from enum import Enum
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    MISSING_PARAMETER = "MISSING_PARAMETER"
    INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    DATABASE_ERROR = "DATABASE_ERROR"
    TASK_ERROR = "TASK_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def create_error_response(code: ErrorCode, message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code.value, "message": message}},
    )


class APIError(HTTPException):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        super().__init__(status_code=status_code, detail={"code": code.value, "message": message})


def api_error_handler(request: Any, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code.value, "message": exc.message}},
    )
