"""Token bucket rate limiter with per-key and per-endpoint tracking.

Provides rate limiting with proper HTTP headers (X-RateLimit-*) and
different limits for different endpoint types.
"""

import logging
import time
import threading
from dataclasses import dataclass, field

logger = logging.getLogger("al_furqan.auth.rate_limiter")


@dataclass
class TokenBucket:
    """Token bucket for rate limiting a single key+endpoint combination."""

    capacity: int  # Max tokens (= requests per window)
    tokens: float  # Current available tokens
    refill_rate: float  # Tokens added per second
    last_refill: float = field(default_factory=time.time)

    def consume(self) -> bool:
        """Try to consume one token. Returns True if allowed, False if rate limited."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    @property
    def remaining(self) -> int:
        """Current remaining tokens (approximate)."""
        now = time.time()
        elapsed = now - self.last_refill
        current = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        return max(0, int(current))

    @property
    def reset_at(self) -> float:
        """Unix timestamp when the bucket will be full again."""
        if self.tokens >= self.capacity:
            return time.time()
        tokens_needed = self.capacity - self.tokens
        return self.last_refill + tokens_needed / self.refill_rate


# Endpoint type → default requests per minute
ENDPOINT_LIMITS = {
    "health": 0,  # Unlimited
    "read": 60,  # GET operations
    "evaluate": 10,  # POST /evaluate (expensive LLM calls)
    "evaluate_dual": 5,  # Dual evaluation (2x LLM calls)
    "write": 30,  # POST/PUT/DELETE general
}


def classify_endpoint(method: str, path: str) -> str:
    """Classify a request into an endpoint type for rate limiting."""
    if "/health" in path:
        return "health"
    if method == "GET":
        return "read"
    if method == "POST" and "/evaluate" in path:
        return "evaluate"
    if method == "POST" and "/criterion-test" in path:
        return "evaluate"
    return "write"


class RateLimiter:
    """Token bucket rate limiter with per-key tracking."""

    def __init__(self, default_rpm: int = 30):
        self.default_rpm = default_rpm
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _get_bucket(
        self, key_id: str, endpoint_type: str, custom_limit: int = 0
    ) -> TokenBucket:
        """Get or create a bucket for a key+endpoint combination."""
        bucket_key = f"{key_id}:{endpoint_type}"

        with self._lock:
            if bucket_key not in self._buckets:
                # Determine limit: custom > endpoint default > global default
                limit = custom_limit or ENDPOINT_LIMITS.get(
                    endpoint_type, self.default_rpm
                )
                if limit == 0:  # Unlimited
                    limit = 999999

                self._buckets[bucket_key] = TokenBucket(
                    capacity=limit,
                    tokens=float(limit),
                    refill_rate=limit / 60.0,  # tokens per second
                )

            return self._buckets[bucket_key]

    def check(
        self, key_id: str, method: str, path: str, custom_limit: int = 0
    ) -> tuple[bool, dict]:  # pylint: disable=line-too-long
        """
        Check if a request is within rate limits.

        Returns:
            (allowed, headers_dict) — headers to include in the response.
        """
        endpoint_type = classify_endpoint(method, path)

        # Health endpoint is always unlimited
        if endpoint_type == "health":
            return True, {}

        bucket = self._get_bucket(key_id, endpoint_type, custom_limit)
        allowed = bucket.consume()

        limit = bucket.capacity
        remaining = bucket.remaining
        reset_at = int(bucket.reset_at)

        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_at),
        }

        if not allowed:
            retry_after = max(1, reset_at - int(time.time()))
            headers["Retry-After"] = str(retry_after)
            logger.warning(
                "RATE_LIMITED key_id=%s endpoint=%s type=%s limit=%d",
                key_id,
                path,
                endpoint_type,
                limit,
            )

        return allowed, headers

    def cleanup_expired(self, max_age_seconds: int = 3600) -> int:
        """Remove stale buckets that haven't been used recently."""
        now = time.time()
        removed = 0
        with self._lock:
            stale_keys = [
                k
                for k, b in self._buckets.items()
                if now - b.last_refill > max_age_seconds
            ]
            for k in stale_keys:
                del self._buckets[k]
                removed += 1
        if removed:
            logger.info("Cleaned up %d stale rate limit buckets", removed)
        return removed
