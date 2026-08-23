"""Tests for the evaluate endpoint with mock LLM."""


class TestEvaluateEndpoint:
    """TestEvaluateEndpoint class."""

    def test_submit_evaluation_success(self, client_no_auth):
        """Test submit_evaluation_success."""
        resp = client_no_auth.post(
            "/api/v1/evaluate",
            json={"question": "Is interest-based lending just?"},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "completed"
        assert data["verdict_id"]
        assert data["verdict"] is not None
        assert data["verdict"]["question"] == "Is interest-based lending just?"
        assert data["verdict"]["total_score"] > 0

    def test_submit_evaluation_with_context(self, client_no_auth):
        """Test submit_evaluation_with_context."""
        resp = client_no_auth.post(
            "/api/v1/evaluate",
            json={
                "question": "Is interest halal?",
                "context": "Islamic finance principles",
            },
        )
        assert resp.status_code == 202
        assert resp.json()["verdict"] is not None

    def test_submit_evaluation_with_options(self, client_no_auth):
        """Test submit_evaluation_with_options."""
        resp = client_no_auth.post(
            "/api/v1/evaluate",
            json={
                "question": "Test question",
                "options": {
                    "include_precedent": False,
                    "auto_approve_threshold": 50,
                },
            },
        )
        assert resp.status_code == 202

    def test_empty_question_rejected(self, client_no_auth):
        """Test empty_question_rejected."""
        resp = client_no_auth.post(
            "/api/v1/evaluate",
            json={"question": ""},
        )
        assert resp.status_code == 422  # Pydantic validation (min_length=1)

    def test_question_too_long_rejected(self, client_no_auth):
        """Test question_too_long_rejected."""
        resp = client_no_auth.post(
            "/api/v1/evaluate",
            json={"question": "x" * 5001},
        )
        assert resp.status_code == 422  # Pydantic max_length=5000

    def test_get_evaluation_status_found(self, client_no_auth):
        """Test get_evaluation_status_found."""
        # First create a verdict
        create_resp = client_no_auth.post(
            "/api/v1/evaluate",
            json={"question": "Test for status check"},
        )
        assert create_resp.status_code == 202
        verdict_id = create_resp.json()["verdict_id"]

        # Now retrieve it
        resp = client_no_auth.get(f"/api/v1/evaluate/{verdict_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["verdict_id"] == verdict_id
        assert data["status"] == "completed"

    def test_get_evaluation_status_not_found(self, client_no_auth):
        """Test get_evaluation_status_not_found."""
        resp = client_no_auth.get("/api/v1/evaluate/nonexistent-id")
        assert resp.status_code == 404


class TestEvaluateAuth:
    """Test evaluate endpoint with auth enabled."""

    def test_evaluate_requires_evaluator_role(self, auth_client):
        """Test evaluate_requires_evaluator_role."""
        client, _admin_key, reader_key, _evaluator_key = auth_client  # pylint: disable=unused-variable
        # Reader cannot evaluate
        resp = client.post(
            "/api/v1/evaluate",
            headers={"X-API-Key": reader_key},
            json={"question": "Test question"},
        )
        assert resp.status_code == 403

    def test_evaluate_admin_can_evaluate(self, auth_client):
        """Test evaluate_admin_can_evaluate."""
        client, admin_key, *_ = auth_client
        resp = client.post(
            "/api/v1/evaluate",
            headers={"X-API-Key": admin_key},
            json={"question": "Is interest halal?"},
        )
        assert resp.status_code == 202
