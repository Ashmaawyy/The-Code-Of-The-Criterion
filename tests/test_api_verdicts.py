"""Tests for verdict CRUD endpoints."""



class TestVerdictListEndpoint:
    """TestVerdictListEndpoint class."""
    def test_list_verdicts_empty(self, client_no_auth):
        """Test list_verdicts_empty."""
        resp = client_no_auth.get("/api/v1/verdicts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["verdicts"] == []

    def test_list_verdicts_after_evaluation(self, client_no_auth):
        """Test list_verdicts_after_evaluation."""
        # Create a verdict first
        client_no_auth.post(
            "/api/v1/evaluate",
            json={"question": "Is interest halal?"},
        )
        resp = client_no_auth.get("/api/v1/verdicts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["verdicts"]) >= 1

    def test_list_verdicts_pagination(self, client_no_auth):
        """Test list_verdicts_pagination."""
        resp = client_no_auth.get("/api/v1/verdicts?limit=5&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["per_page"] == 5

    def test_list_verdicts_filter_status(self, client_no_auth):
        """Test list_verdicts_filter_status."""
        resp = client_no_auth.get("/api/v1/verdicts?status=approved")
        assert resp.status_code == 200


class TestVerdictGetEndpoint:
    """TestVerdictGetEndpoint class."""
    def test_get_verdict_found(self, client_no_auth):
        """Test get_verdict_found."""
        # Create first
        create_resp = client_no_auth.post(
            "/api/v1/evaluate",
            json={"question": "Test for get"},
        )
        verdict_id = create_resp.json()["verdict_id"]

        resp = client_no_auth.get(f"/api/v1/verdicts/{verdict_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == verdict_id

    def test_get_verdict_not_found(self, client_no_auth):
        """Test get_verdict_not_found."""
        resp = client_no_auth.get("/api/v1/verdicts/nonexistent-id")
        assert resp.status_code == 404


class TestVerdictDeleteEndpoint:
    """TestVerdictDeleteEndpoint class."""
    def test_delete_verdict_found(self, client_no_auth):
        """Test delete_verdict_found."""
        create_resp = client_no_auth.post(
            "/api/v1/evaluate",
            json={"question": "Test for delete"},
        )
        verdict_id = create_resp.json()["verdict_id"]

        resp = client_no_auth.delete(f"/api/v1/verdicts/{verdict_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["verdict_id"] == verdict_id
        assert data["status"] == "invalidated"

    def test_delete_verdict_not_found(self, client_no_auth):
        """Test delete_verdict_not_found."""
        resp = client_no_auth.delete("/api/v1/verdicts/nonexistent-id")
        assert resp.status_code == 404


class TestVerdictSearchEndpoint:
    """TestVerdictSearchEndpoint class."""
    def test_search_verdicts(self, client_no_auth):
        """Test search_verdicts."""
        # Create a verdict first
        client_no_auth.post(
            "/api/v1/evaluate",
            json={"question": "Is interest-based lending just?"},
        )
        resp = client_no_auth.get("/api/v1/verdicts/search?q=interest&limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_search_verdicts_empty_query(self, client_no_auth):
        """Test search_verdicts_empty_query."""
        resp = client_no_auth.get("/api/v1/verdicts/search?q=")
        # Should fail validation (min_length=1)
        assert resp.status_code == 422
