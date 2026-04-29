"""Tests for API Key Authentication — valid/invalid/missing/revoked/roles."""



class TestAuthMissingKey:
    """Test that protected endpoints reject requests without API keys."""

    def test_missing_key_returns_401(self, auth_client):
        """Test missing_key_returns_401."""
        client, admin_key, reader_key, _evaluator_key = auth_client  # pylint: disable=unused-variable
        resp = client.get("/api/v1/verdicts")
        assert resp.status_code == 401
        body = resp.json()
        assert body["error"]["code"] == "INVALID_API_KEY"

    def test_missing_key_health_exempt(self, auth_client):
        """Health and root endpoints should be exempt from auth."""
        client, *_ = auth_client
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Al-Furqan" in resp.json()["name"]

    def test_missing_key_docs_exempt(self, auth_client):
        """Test missing_key_docs_exempt."""
        client, *_ = auth_client
        resp = client.get("/docs")
        assert resp.status_code == 200


class TestAuthInvalidKey:
    """Test that invalid keys are rejected."""

    def test_invalid_key_returns_401(self, auth_client):
        """Test invalid_key_returns_401."""
        client, *_ = auth_client
        resp = client.get(
            "/api/v1/verdicts",
            headers={"X-API-Key": "afk_live_invalidkey12345678"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "INVALID_API_KEY"

    def test_malformed_key_returns_401(self, auth_client):
        """Test malformed_key_returns_401."""
        client, *_ = auth_client
        resp = client.get(
            "/api/v1/verdicts",
            headers={"X-API-Key": "not-even-a-real-key"},
        )
        assert resp.status_code == 401

    def test_bearer_auth_works(self, auth_client):
        """Test bearer_auth_works."""
        client, admin_key, *_ = auth_client
        resp = client.get(
            "/api/v1/verdicts",
            headers={"Authorization": f"Bearer {admin_key}"},
        )
        assert resp.status_code == 200


class TestAuthRevokedKey:  # pylint: disable=too-few-public-methods
    """Test that revoked keys are rejected."""

    def test_revoked_key_returns_401(self, auth_client):
        """Test revoked_key_returns_401."""
        client, admin_key, reader_key, _evaluator_key = auth_client  # pylint: disable=unused-variable

        # Create a new key to revoke
        km = client.app.state.key_manager
        raw_key, api_key = km.create_key("revoke-test", role="admin")

        # Key works before revocation
        resp = client.get("/api/v1/verdicts", headers={"X-API-Key": raw_key})
        assert resp.status_code == 200

        # Revoke
        km.revoke_key(api_key.key_id)

        # Key no longer works
        resp = client.get("/api/v1/verdicts", headers={"X-API-Key": raw_key})
        assert resp.status_code == 401


class TestAuthRoles:
    """Test role-based access control."""

    def test_reader_can_get(self, auth_client):
        """Test reader_can_get."""
        client, admin_key, reader_key, _evaluator_key = auth_client  # pylint: disable=unused-variable
        resp = client.get(
            "/api/v1/verdicts",
            headers={"X-API-Key": reader_key},
        )
        assert resp.status_code == 200

    def test_reader_cannot_post_evaluate(self, auth_client):
        """Test reader_cannot_post_evaluate."""
        client, admin_key, reader_key, _evaluator_key = auth_client  # pylint: disable=unused-variable
        resp = client.post(
            "/api/v1/evaluate",
            headers={"X-API-Key": reader_key},
            json={"question": "Is interest halal?"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "INSUFFICIENT_ROLE"

    def test_evaluator_can_post_evaluate(self, auth_client):
        """Test evaluator_can_post_evaluate."""
        client, admin_key, reader_key, evaluator_key = auth_client  # pylint: disable=unused-variable
        resp = client.post(
            "/api/v1/evaluate",
            headers={"X-API-Key": evaluator_key},
            json={"question": "Is interest halal?"},
        )
        # Should be 202 (accepted) if evaluation succeeds
        assert resp.status_code in (200, 202)

    def test_admin_can_delete(self, auth_client):
        """Test admin_can_delete."""
        client, admin_key, reader_key, _evaluator_key = auth_client  # pylint: disable=unused-variable
        # Try delete (will 404 because no verdicts, but not 403)
        resp = client.delete(
            "/api/v1/verdicts/nonexistent",
            headers={"X-API-Key": admin_key},
        )
        assert resp.status_code == 404  # Not 403

    def test_reader_cannot_delete(self, auth_client):
        """Test reader_cannot_delete."""
        client, admin_key, reader_key, _evaluator_key = auth_client  # pylint: disable=unused-variable
        resp = client.delete(
            "/api/v1/verdicts/some-id",
            headers={"X-API-Key": reader_key},
        )
        assert resp.status_code == 403

    def test_options_exempt(self, auth_client):
        """CORS preflight (OPTIONS) should not require auth."""
        client, *_ = auth_client
        resp = client.options("/api/v1/verdicts")
        # Should not be 401
        assert resp.status_code != 401
