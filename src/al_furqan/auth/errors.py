"""Structured error responses for the Al-Furqan API.

Provides consistent error formatting across all endpoints with
machine-readable error codes and human-readable messages.
"""

from enum import Enum
from typing import Any, Optional

from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    """Machine-readable error codes for API responses."""

    INVALID_API_KEY = "INVALID_API_KEY"
    INSUFFICIENT_ROLE = "INSUFFICIENT_ROLE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INVALID_REQUEST = "INVALID_REQUEST"
    QUESTION_TOO_LONG = "QUESTION_TOO_LONG"
    EVALUATION_FAILED = "EVALUATION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    BODY_TOO_LARGE = "BODY_TOO_LARGE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    NOT_FOUND = "NOT_FOUND"
    BAD_REQUEST = "BAD_REQUEST"
    VALIDATION_ERROR = "VALIDATION_ERROR"


def error_response(
    status_code: int,
    code: ErrorCode,
    message: str,
    details: Optional[dict[str, Any]] = None,
) -> JSONResponse:
    """Build a structured JSON error response.

    Format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable message",
            "details": { ... }  // optional
        }
    }
    """
    body: dict[str, Any] = {
        "error": {
            "code": code.value,
            "message": message,
        }
    }
    if details:
        body["error"]["details"] = details

    return JSONResponse(status_code=status_code, content=body)
