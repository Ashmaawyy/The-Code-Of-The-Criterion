"""Tests for health and root endpoints."""



class TestRootEndpoint:
    """TestRootEndpoint class."""
    def test_root_returns_info(self, client_no_auth):
        """Test root_returns_info."""
        resp = client_no_auth.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Al-Furqan — The Criterion"
        assert data["version"] == "0.1.0"
        assert "docs" in data
        assert "api" in data

    def test_root_no_auth_required(self, auth_client):
        """Root should be accessible without auth even when auth is enabled."""
        client, *_ = auth_client
        resp = client.get("/")
        assert resp.status_code == 200


class TestHealthEndpoint:
    """TestHealthEndpoint class."""
    def test_health_returns_status(self, client_no_auth):
        """Test health_returns_status."""
        resp = client_no_auth.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert data["status"] in ("healthy", "degraded", "unhealthy")
        assert "llm_status" in data
        assert "store_status" in data
        assert data["version"] == "0.1.0"

    def test_health_no_auth_required(self, auth_client):
        """Health should be accessible without auth."""
        client, *_ = auth_client
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
