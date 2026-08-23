"""Tests for security middleware — headers, body size limits, content-type validation."""


class TestSecurityHeaders:
    """Test that security headers are present on all responses."""

    def test_security_headers_on_root(self, client_no_auth):
        """Test security_headers_on_root."""
        resp = client_no_auth.get("/")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "default-src" in resp.headers.get("Content-Security-Policy", "")
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_security_headers_on_api(self, client_no_auth):
        """Test security_headers_on_api."""
        resp = client_no_auth.get("/api/v1/verdicts")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_security_headers_with_auth(self, auth_client):
        """Test security_headers_with_auth."""
        client, _admin_key, *_ = auth_client
        resp = client.get("/")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"


class TestBodySizeLimit:
    """Test that oversized request bodies are rejected."""

    def test_oversized_body_rejected(self, client_no_auth):
        """Test oversized_body_rejected."""
        # 64KB limit, send 100KB
        huge_body = {"question": "x" * (100 * 1024)}
        resp = client_no_auth.post(
            "/api/v1/evaluate",
            json=huge_body,
            headers={"Content-Length": str(100 * 1024)},
        )
        assert resp.status_code == 413
        assert resp.json()["error"]["code"] == "BODY_TOO_LARGE"

    def test_normal_body_accepted(self, client_no_auth):
        """Test normal_body_accepted."""
        resp = client_no_auth.post(
            "/api/v1/evaluate",
            json={"question": "Is interest halal?"},
        )
        # Should not be 413
        assert resp.status_code != 413


class TestContentTypeValidation:
    """Test content-type validation for POST requests."""

    def test_wrong_content_type_rejected(self, client_no_auth):
        """Test wrong_content_type_rejected."""
        resp = client_no_auth.post(
            "/api/v1/evaluate",
            content="question=test",
            headers={"Content-Type": "text/plain"},
        )
        assert resp.status_code == 415
        assert resp.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"

    def test_json_content_type_accepted(self, client_no_auth):
        """Test json_content_type_accepted."""
        resp = client_no_auth.post(
            "/api/v1/evaluate",
            json={"question": "Is interest halal?"},
        )
        assert resp.status_code != 415
