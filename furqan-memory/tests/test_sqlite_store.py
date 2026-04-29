"""Tests for SQLite storage layer."""

import time

import pytest

from furqan_memory.storage.sqlite_store import MemoryStore

# pylint: disable=redefined-outer-name


@pytest.fixture
def store(tmp_path):
    """Create a fresh MemoryStore for each test."""
    db_path = str(tmp_path / "test_memory.db")
    s = MemoryStore(db_path)
    yield s
    s.close()


# ---- Verdict CRUD ----

class TestVerdictCRUD:
    """TestVerdictCRUD class."""
    def test_save_and_get_verdict(self, store):
        """Test save_and_get_verdict."""
        verdict_data = {
            "total_score": 85,
            "gate_results": [{"gate": "scriptural", "score": 90}],
            "final_judgment": "Accepted",
        }
        vid = store.save_verdict("v_001", "Is charity obligatory?", verdict_data)
        assert vid == "v_001"

        result = store.get_verdict("v_001")
        assert result is not None
        assert result["question"] == "Is charity obligatory?"
        assert result["verdict_data"]["total_score"] == 85
        assert result["final_judgment"] == "Accepted"

    def test_get_nonexistent_verdict(self, store):
        """Test get_nonexistent_verdict."""
        assert store.get_verdict("nonexistent") is None

    def test_save_verdict_with_tags(self, store):
        """Test save_verdict_with_tags."""
        verdict_data = {"total_score": 70, "final_judgment": "Cautious"}
        store.save_verdict("v_002", "Test?", verdict_data, tags=["fiqh", "salah"])
        result = store.get_verdict("v_002")
        assert result["tags"] == ["fiqh", "salah"]

    def test_get_recent_verdicts(self, store):
        """Test get_recent_verdicts."""
        for i in range(5):
            store.save_verdict(
                f"v_{i:03d}", f"Question {i}",
                {"total_score": i * 10, "final_judgment": f"J{i}"},
            )
            time.sleep(0.01)  # ensure ordering

        recent = store.get_recent_verdicts(limit=3)
        assert len(recent) == 3
        # Most recent first
        assert recent[0]["id"] == "v_004"

    def test_get_recent_verdicts_filtered_by_domain(self, store):
        """Test get_recent_verdicts_filtered_by_domain."""
        store.save_verdict("v_a", "Q1", {"total_score": 1}, domain="islamic")
        store.save_verdict("v_b", "Q2", {"total_score": 2}, domain="medical")
        store.save_verdict("v_c", "Q3", {"total_score": 3}, domain="islamic")

        islamic = store.get_recent_verdicts(limit=10, domain="islamic")
        assert len(islamic) == 2
        assert all(v["domain"] == "islamic" for v in islamic)

    def test_search_verdicts(self, store):
        """Test search_verdicts."""
        store.save_verdict("v_x", "Is riba (interest) haram?", {"total_score": 95})
        store.save_verdict("v_y", "What about fasting?", {"total_score": 80})

        results = store.search_verdicts("riba")
        assert len(results) == 1
        assert results[0]["id"] == "v_x"

    def test_access_count_increments(self, store):
        """Test access_count_increments."""
        store.save_verdict("v_ac", "Test access", {"total_score": 50})
        store.get_verdict("v_ac")
        store.get_verdict("v_ac")
        result = store.get_verdict("v_ac")
        assert result["access_count"] == 2  # third get sees count from first two


# ---- Pattern CRUD ----

class TestPatternCRUD:
    """TestPatternCRUD class."""
    def test_save_and_get_pattern(self, store):
        """Test save_and_get_pattern."""
        pattern = {
            "id": "p_001",
            "category": "fiqh",
            "rule": "Interest-based transactions are prohibited",
            "signals": ["riba", "interest", "usury"],
            "expected_gates": ["scriptural", "logical"],
            "confidence": 0.9,
        }
        pid = store.save_pattern(pattern)
        assert pid == "p_001"

        result = store.get_pattern("p_001")
        assert result is not None
        assert result["category"] == "fiqh"
        assert result["confidence"] == 0.9
        assert "riba" in result["signals"]

    def test_get_nonexistent_pattern(self, store):
        """Test get_nonexistent_pattern."""
        assert store.get_pattern("nonexistent") is None

    def test_get_mature_patterns(self, store):  # pylint: disable=line-too-long
        """Test get_mature_patterns."""  # pylint: disable=line-too-long
        store.save_pattern({"id": "p_low", "category": "a", "rule": "low", "signals": [], "expected_gates": [], "confidence": 0.3})  # pylint: disable=line-too-long
        store.save_pattern({"id": "p_mid", "category": "b", "rule": "mid", "signals": [], "expected_gates": [], "confidence": 0.7})
        store.save_pattern({"id": "p_high", "category": "c", "rule": "high", "signals": [], "expected_gates": [], "confidence": 0.95})

        mature = store.get_mature_patterns(min_confidence=0.8)
        assert len(mature) == 1
        assert mature[0]["id"] == "p_high"

    def test_update_pattern(self, store):
        """Test update_pattern."""
        store.save_pattern({
            "id": "p_upd", "category": "test", "rule": "r",
            "signals": [], "expected_gates": [],
            "confidence": 0.5,
        })
        updated = store.update_pattern("p_upd", {"confidence": 0.85, "hit_count": 10})
        assert updated is True

        result = store.get_pattern("p_upd")
        assert result["confidence"] == 0.85
        assert result["hit_count"] == 10

    def test_update_nonexistent_pattern(self, store):
        """Test update_nonexistent_pattern."""
        assert store.update_pattern("nonexistent", {"confidence": 1.0}) is False


# ---- Feedback CRUD ----

class TestFeedbackCRUD:
    """TestFeedbackCRUD class."""
    def test_save_and_get_feedback(self, store):
        """Test save_and_get_feedback."""
        fid = store.save_feedback("v_001", "verdict", "positive", "Good answer")
        assert fid.startswith("f_")

        fb_list = store.get_feedback_for("v_001")
        assert len(fb_list) == 1
        assert fb_list[0]["rating"] == "positive"
        assert fb_list[0]["correction"] == "Good answer"

    def test_multiple_feedback(self, store):
        """Test multiple_feedback."""
        store.save_feedback("v_002", "verdict", "positive")
        store.save_feedback("v_002", "verdict", "negative", "Wrong source")

        fb_list = store.get_feedback_for("v_002")
        assert len(fb_list) == 2

    def test_no_feedback(self, store):
        """Test no_feedback."""
        assert store.get_feedback_for("nonexistent") == []


# ---- Stats ----

class TestStats:
    """TestStats class."""
    def test_empty_stats(self, store):
        """Test empty_stats."""
        stats = store.get_stats()
        assert stats["verdicts"] == 0
        assert stats["patterns"] == 0
        assert stats["feedback_entries"] == 0
        assert stats["mature_patterns"] == 0

    def test_stats_with_data(self, store):
        """Test stats_with_data."""
        store.save_verdict("v_1", "Q1", {"total_score": 80})
        store.save_verdict("v_2", "Q2", {"total_score": 90})
        store.save_pattern({
            "id": "p_1", "category": "a", "rule": "r",
            "signals": [], "expected_gates": [],
            "confidence": 0.9,
        })
        store.save_feedback("v_1", "verdict", "positive")

        stats = store.get_stats()
        assert stats["verdicts"] == 2
        assert stats["patterns"] == 1
        assert stats["mature_patterns"] == 1
        assert stats["feedback_entries"] == 1

    def test_stats_filtered_by_domain(self, store):
        """Test stats_filtered_by_domain."""
        store.save_verdict("v_a", "Q1", {"total_score": 1}, domain="islamic")
        store.save_verdict("v_b", "Q2", {"total_score": 2}, domain="medical")

        stats = store.get_stats(domain="islamic")
        assert stats["verdicts"] == 1
        assert stats["domain"] == "islamic"
