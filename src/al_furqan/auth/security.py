"""Security middleware — headers, body size limits, content-type validation.

Adds security headers to all responses and enforces request body size limits.
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("al_furqan.auth.security")

# Default max body size: 64KB
DEFAULT_MAX_BODY_SIZE = 64 * 1024

# Security headers applied to all responses
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Content-Security-Policy": "default-src 'none'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):  # pylint: disable=too-few-public-methods
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        """Execute dispatch."""
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):  # pylint: disable=too-few-public-methods
    """Reject requests with bodies exceeding the configured size limit."""

    def __init__(self, app, max_body_size: int = DEFAULT_MAX_BODY_SIZE):
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next):
        """Execute dispatch."""
        # Only check body size for methods that have bodies
        if request.method in ("POST", "PUT", "PATCH"):
            # Check Content-Length header if present
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_body_size:
                logger.warning(
                    "BODY_TOO_LARGE content_length=%s max=%d path=%s",
                    content_length,
                    self.max_body_size,
                    request.url.path,
                )
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": {
                            "code": "BODY_TOO_LARGE",
                            "message": f"Request body too large. Maximum size is {self.max_body_size} bytes.",  # pylint: disable=line-too-long
                        }
                    },
                )

            # Validate Content-Type for POST/PUT/PATCH
            content_type = request.headers.get("content-type", "")
            path = request.url.path
            # Skip content-type check for docs/openapi/root endpoints
            if path not in ("/", "/docs", "/redoc", "/openapi.json"):
                if content_type and "application/json" not in content_type:
                    # Allow multipart/form-data for file uploads if needed in the future
                    if "multipart/form-data" not in content_type:
                        return JSONResponse(
                            status_code=415,
                            content={
                                "error": {
                                    "code": "UNSUPPORTED_MEDIA_TYPE",
                                    "message": "Content-Type must be application/json.",
                                }
                            },
                        )

        response = await call_next(request)
        return response
