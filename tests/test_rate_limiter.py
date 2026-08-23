"""Tests for rate limiting — under/over limit, headers, per-key isolation."""

import time

from al_furqan.auth.rate_limiter import RateLimiter, TokenBucket, classify_endpoint


class TestClassifyEndpoint:
    """TestClassifyEndpoint class."""

    def test_health(self):
        """Test health."""
        assert classify_endpoint("GET", "/api/v1/health") == "health"

    def test_get_read(self):
        """Test get_read."""
        assert classify_endpoint("GET", "/api/v1/verdicts") == "read"

    def test_post_evaluate(self):
        """Test post_evaluate."""
        assert classify_endpoint("POST", "/api/v1/evaluate") == "evaluate"

    def test_post_criterion(self):
        """Test post_criterion."""
        assert classify_endpoint("POST", "/api/v1/criterion-test") == "evaluate"

    def test_post_generic(self):
        """Test post_generic."""
        assert classify_endpoint("POST", "/api/v1/verdicts/x/review") == "write"


class TestTokenBucket:
    """TestTokenBucket class."""

    def test_consume_under_limit(self):
        """Test consume_under_limit."""
        bucket = TokenBucket(capacity=5, tokens=5.0, refill_rate=5.0 / 60)
        for _ in range(5):
            assert bucket.consume() is True

    def test_consume_over_limit(self):
        """Test consume_over_limit."""
        bucket = TokenBucket(capacity=2, tokens=2.0, refill_rate=2.0 / 60)
        assert bucket.consume() is True
        assert bucket.consume() is True
        assert bucket.consume() is False

    def test_remaining(self):
        """Test remaining."""
        bucket = TokenBucket(capacity=10, tokens=10.0, refill_rate=10.0 / 60)
        bucket.consume()
        assert bucket.remaining >= 8  # Approx, due to refill

    def test_reset_at(self):
        """Test reset_at."""
        bucket = TokenBucket(capacity=2, tokens=0.0, refill_rate=2.0 / 60)
        reset = bucket.reset_at
        assert reset > time.time()


class TestRateLimiter:
    """TestRateLimiter class."""

    def test_under_limit_allowed(self):
        """Test under_limit_allowed."""
        rl = RateLimiter(default_rpm=10)
        allowed, headers = rl.check("key1", "GET", "/api/v1/verdicts")
        assert allowed is True
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers

    def test_over_limit_blocked(self):
        """Test over_limit_blocked."""
        rl = RateLimiter(default_rpm=2)
        # Use custom_limit=2 to override endpoint defaults
        rl.check("key1", "POST", "/api/v1/something", custom_limit=2)
        rl.check("key1", "POST", "/api/v1/something", custom_limit=2)
        allowed, headers = rl.check("key1", "POST", "/api/v1/something", custom_limit=2)
        assert allowed is False
        assert "Retry-After" in headers

    def test_health_unlimited(self):
        """Test health_unlimited."""
        rl = RateLimiter(default_rpm=1)
        for _ in range(100):
            allowed, _ = rl.check("key1", "GET", "/api/v1/health")
            assert allowed is True

    def test_per_key_isolation(self):
        """Test per_key_isolation."""
        rl = RateLimiter(default_rpm=2)
        # Key1 uses its limit (custom_limit=2 to override endpoint defaults)
        rl.check("key1", "POST", "/api/v1/something", custom_limit=2)
        rl.check("key1", "POST", "/api/v1/something", custom_limit=2)
        allowed1, _ = rl.check("key1", "POST", "/api/v1/something", custom_limit=2)
        assert allowed1 is False

        # Key2 should still have its own limit
        allowed2, _ = rl.check("key2", "POST", "/api/v1/something", custom_limit=2)
        assert allowed2 is True

    def test_rate_limit_headers_format(self):
        """Test rate_limit_headers_format."""
        rl = RateLimiter(default_rpm=10)
        _, headers = rl.check("key1", "GET", "/api/v1/verdicts")
        assert int(headers["X-RateLimit-Limit"]) > 0
        assert int(headers["X-RateLimit-Remaining"]) >= 0
        assert int(headers["X-RateLimit-Reset"]) > 0

    def test_cleanup_expired(self):
        """Test cleanup_expired."""
        rl = RateLimiter(default_rpm=10)
        rl.check("old-key", "GET", "/api/v1/verdicts")
        # Force the bucket to appear old
        for bucket in rl._buckets.values():  # pylint: disable=protected-access
            bucket.last_refill = time.time() - 7200
        removed = rl.cleanup_expired(max_age_seconds=3600)
        assert removed > 0

    def test_custom_limit(self):
        """Test custom_limit."""
        rl = RateLimiter(default_rpm=100)
        # Custom limit of 1
        rl.check("key1", "GET", "/api/v1/verdicts", custom_limit=1)
        allowed, _ = rl.check("key1", "GET", "/api/v1/verdicts", custom_limit=1)
        assert allowed is False


# pylint: disable=too-few-public-methods
class TestRateLimitIntegration:
    """Test rate limiting via the full API."""

    def test_rate_limit_headers_in_response(self, auth_client):
        """Test rate_limit_headers_in_response."""
        client, _admin_key, *_ = auth_client
        resp = client.get(
            "/api/v1/verdicts",
            headers={"X-API-Key": _admin_key},
        )
        assert resp.status_code == 200
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers
