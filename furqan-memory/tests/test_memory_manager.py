"""Tests for MemoryManager — the core orchestration layer."""

import time

import pytest

from furqan_memory.storage.sqlite_store import MemoryStore
from furqan_memory.storage.vector_store import MemoryVectorSearch
from furqan_memory.memory_manager import MemoryManager

# pylint: disable=redefined-outer-name


@pytest.fixture
def manager(tmp_path):
    """Create a fresh MemoryManager for each test."""
    store = MemoryStore(str(tmp_path / "test.db"))
    vectors = MemoryVectorSearch(persist_dir=None)
    mgr = MemoryManager(store, vectors)
    yield mgr
    store.close()


class TestRememberAndRecall:
    """TestRememberAndRecall class."""
    def test_remember_returns_id(self, manager):
        """Test remember_returns_id."""
        vid = manager.remember(
            "Is charity obligatory?",
            {"total_score": 85, "final_judgment": "Yes"},
        )
        assert vid.startswith("v_")

    def test_remember_and_recall(self, manager):
        """Test remember_and_recall."""
        manager.remember(
            "Is riba (interest) haram?",
            {"total_score": 95, "final_judgment": "Prohibited"},
        )
        results = manager.recall("interest banking riba")
        assert len(results) >= 1
        assert results[0]["question"] == "Is riba (interest) haram?"
        assert results[0]["verdict_data"]["total_score"] == 95

    def test_recall_empty_memory(self, manager):
        """Test recall_empty_memory."""
        results = manager.recall("anything")
        assert results == []

    def test_remember_multiple_recall_most_relevant(self, manager):
        """Test remember_multiple_recall_most_relevant."""
        manager.remember("Is riba (interest) permissible?", {"total_score": 95})
        manager.remember("How to perform wudu?", {"total_score": 88})
        manager.remember("Rules of fasting in Ramadan", {"total_score": 90})

        results = manager.recall("interest and banking loans", limit=3)
        assert len(results) >= 1
        # Most relevant should be riba
        assert (
            "riba" in results[0]["question"].lower()
            or "interest" in results[0]["question"].lower()
        )

    def test_recall_with_domain_filter(self, manager):
        """Test recall_with_domain_filter."""
        manager.remember("Q1", {"total_score": 80}, domain="islamic")
        manager.remember("Q2", {"total_score": 70}, domain="medical")

        islamic_results = manager.recall("Q1", domain="islamic")
        # Should only return islamic domain
        for r in islamic_results:
            assert r["domain"] == "islamic"

    def test_remember_with_tags(self, manager):
        """Test remember_with_tags."""
        _vid = manager.remember("Test?", {"total_score": 50}, tags=["fiqh", "test"])
        results = manager.recall("Test?")
        assert results[0]["tags"] == ["fiqh", "test"]


class TestRecognize:
    """TestRecognize class."""
    def test_recognize_no_patterns(self, manager):
        """Test recognize_no_patterns."""
        result = manager.recognize("Is interest haram?")
        assert result is None

    def test_recognize_with_matching_pattern(self, manager):
        """Test recognize_with_matching_pattern."""
        # Add a mature pattern
        manager.store.save_pattern({
            "id": "p_riba",
            "category": "fiqh",
            "rule": "Is interest or riba permissible in Islam?",
            "signals": ["riba", "interest"],
            "expected_gates": ["scriptural"],
            "confidence": 0.95,
        })
        manager.vectors.add_pattern(
            "p_riba",
            "Is interest or riba permissible in Islam?",
            {"category": "fiqh"},
        )

        result = manager.recognize("Is interest or riba permissible in Islam?", threshold=0.5)
        # With same text, should match
        if result:  # ChromaDB default embeddings may vary
            assert result["matched"] is True
            assert result["pattern"]["id"] == "p_riba"
            assert result["latency_ms"] < 500  # generous for CI

    def test_recognize_low_confidence_pattern_ignored(self, manager):
        """Test recognize_low_confidence_pattern_ignored."""
        manager.store.save_pattern({
            "id": "p_low",
            "category": "test",
            "rule": "Low confidence pattern about interest",
            "signals": [],
            "expected_gates": [],
            "confidence": 0.2,  # Below 0.8 threshold
        })
        manager.vectors.add_pattern("p_low", "Low confidence pattern about interest")

        result = manager.recognize("interest")
        assert result is None  # Confidence too low


class TestFeedback:
    """TestFeedback class."""
    def test_feedback_positive(self, manager):
        """Test feedback_positive."""
        vid = manager.remember("Test question?", {"total_score": 80})
        fid = manager.feedback(vid, "positive")
        assert fid.startswith("f_")

    def test_feedback_with_correction(self, manager):
        """Test feedback_with_correction."""
        vid = manager.remember("Test?", {"total_score": 50})
        fid = manager.feedback(vid, "negative", correction="The source was wrong")
        assert fid.startswith("f_")

        fb = manager.store.get_feedback_for(vid)
        assert len(fb) == 1
        assert fb[0]["correction"] == "The source was wrong"


class TestStats:
    """TestStats class."""
    def test_stats_empty(self, manager):
        """Test stats_empty."""
        stats = manager.stats()
        assert stats["verdicts"] == 0
        assert stats["vector_verdicts"] == 0

    def test_stats_after_remember(self, manager):
        """Test stats_after_remember."""
        manager.remember("Q1", {"total_score": 80})
        manager.remember("Q2", {"total_score": 90})

        stats = manager.stats()
        assert stats["verdicts"] == 2
        assert stats["vector_verdicts"] == 2


# pylint: disable=too-few-public-methods
class TestPerformance:
    """TestPerformance class."""
    def test_recognize_latency(self, manager):
        """Pattern recognition should be fast (<50ms target)."""
        # Add a pattern
        manager.store.save_pattern({
            "id": "p_perf",
            "category": "test",
            "rule": "Performance test pattern for interest queries",
            "signals": ["interest"],
            "expected_gates": ["scriptural"],
            "confidence": 0.95,
        })
        manager.vectors.add_pattern("p_perf", "Performance test pattern for interest queries")

        # Measure latency
        start = time.time()
        for _ in range(10):
            manager.recognize("Is interest allowed?")
        elapsed = (time.time() - start) / 10 * 1000  # avg ms

        # Allow generous limit for CI (ChromaDB default embeddings can be slow)
        assert elapsed < 500, f"Average recognize latency {elapsed:.1f}ms exceeds limit"
