"""API Key Authentication Middleware for FastAPI.

Validates API keys from X-API-Key header or Authorization: Bearer header.
Enforces role-based access control (reader/evaluator/admin).
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from al_furqan.auth.key_manager import KeyManager
from al_furqan.auth.models import APIKey
from al_furqan.auth.rate_limiter import RateLimiter

logger = logging.getLogger("al_furqan.auth.middleware")

# Endpoints that do NOT require authentication
EXEMPT_PATHS = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/health",
}

# Endpoints that only need evaluator+ role for POST
EVALUATOR_POST_PATHS = {
    "/api/v1/evaluate",
    "/api/v1/criterion-test",
}


class APIKeyMiddleware(BaseHTTPMiddleware):  # pylint: disable=too-few-public-methods
    """FastAPI middleware that validates API keys and enforces RBAC."""

    def __init__(
        self,
        app,
        key_manager: KeyManager,
        auth_enabled: bool = True,
        rate_limiter: RateLimiter | None = None,
    ):
        super().__init__(app)
        self.key_manager = key_manager
        self.auth_enabled = auth_enabled
        self.rate_limiter = rate_limiter or RateLimiter()

    def _extract_key(self, request: Request) -> str | None:
        """Extract the API key from request headers."""
        # Try X-API-Key header first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key

        # Try Authorization: Bearer <key>
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:].strip()

        return None

    def _is_exempt(self, path: str) -> bool:
        """Check if the path is exempt from authentication."""
        return path in EXEMPT_PATHS

    def _check_role_permission(self, api_key: APIKey, method: str, path: str) -> bool:  # pylint: disable=too-many-return-statements
        """Check if the key's role has permission for this method+path."""
        # Admin can do everything
        if api_key.role == "admin":
            return True

        # Evaluator can POST to evaluate endpoints and use GET
        if api_key.role == "evaluator":
            if method == "GET":
                return True
            if method == "POST" and any(
                path.startswith(p) for p in EVALUATOR_POST_PATHS
            ):
                return True
            if (
                method == "POST"
                and path.startswith("/api/v1/verdicts")
                and path.endswith("/review")
            ):  # pylint: disable=line-too-long
                return True
            return False

        # Reader: GET only
        if api_key.role == "reader":
            return method == "GET"

        return False

    async def dispatch(self, request: Request, call_next):  # pylint: disable=too-many-return-statements
        """Process the request through auth checks."""
        path = request.url.path
        method = request.method

        # Skip auth for exempt paths and OPTIONS (CORS preflight)
        if self._is_exempt(path) or method == "OPTIONS":
            response = await call_next(request)
            return response

        # Skip auth if disabled
        if not self.auth_enabled:
            response = await call_next(request)
            return response

        # Extract and validate API key
        raw_key = self._extract_key(request)
        if not raw_key:
            logger.warning(
                "AUTH_REJECTED: missing_key endpoint=%s method=%s ip=%s",
                path,
                method,
                request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "INVALID_API_KEY",
                        "message": "API key is required. Provide it via X-API-Key header or Authorization: Bearer header.",  # pylint: disable=line-too-long
                    }
                },
            )

        api_key = self.key_manager.validate_key(raw_key)
        if not api_key:
            logger.warning(
                "AUTH_REJECTED: invalid_key endpoint=%s method=%s ip=%s",
                path,
                method,
                request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "INVALID_API_KEY",
                        "message": "Invalid or revoked API key.",
                    }
                },
            )

        # Check role-based permissions
        if not self._check_role_permission(api_key, method, path):
            logger.warning(
                "AUTH_REJECTED: insufficient_role key_id=%s role=%s endpoint=%s method=%s",
                api_key.key_id,
                api_key.role,
                path,
                method,
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "INSUFFICIENT_ROLE",
                        "message": f"Role '{api_key.role}' does not have permission for {method} {path}.",  # pylint: disable=line-too-long
                    }
                },
            )

        # Attach key info to request state for downstream use
        request.state.api_key = api_key

        # Rate limiting
        allowed, rate_headers = self.rate_limiter.check(
            key_id=api_key.key_id,
            method=method,
            path=path,
            custom_limit=api_key.rate_limit,
        )

        if not allowed:
            logger.warning(
                "RATE_LIMITED key_id=%s endpoint=%s method=%s",
                api_key.key_id,
                path,
                method,
            )
            resp = JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded. Try again later.",
                        "details": {
                            "limit": int(rate_headers.get("X-RateLimit-Limit", 0)),
                            "reset_at": int(rate_headers.get("X-RateLimit-Reset", 0)),
                        },
                    }
                },
            )
            for k, v in rate_headers.items():
                resp.headers[k] = v
            return resp

        # Log successful auth
        logger.info(
            "API_KEY_AUTH key_id=%s role=%s endpoint=%s method=%s ip=%s status=accepted",
            api_key.key_id,
            api_key.role,
            path,
            method,
            request.client.host if request.client else "unknown",
        )

        response = await call_next(request)

        # Add rate limit headers to successful responses
        for k, v in rate_headers.items():
            response.headers[k] = v

        return response
