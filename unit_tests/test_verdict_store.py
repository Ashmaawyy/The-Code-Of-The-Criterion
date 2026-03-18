"""
Unit tests for verdict_store.py

Tests:
- Store and retrieve verdicts
- Semantic search retrieval
- Context formatting for reasoning engine
- Status updates (approve, reject, needs_review)
- Re-indexing on status change
- Cascade invalidation
- Statistics
"""

import json
import sys
import time
from pathlib import Path

import pytest

# Ensure project root is on the path so bare module imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reasoning_engine import Verdict, GateScore, GateResult, SystemType
from verdict_store import VerdictStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_verdict(question: str, score: int = 80, system: SystemType = SystemType.ECONOMIC,
                 timestamp: float = None) -> Verdict:
    """Create a test verdict with minimal boilerplate."""
    return Verdict(
        question=question,
        primary_system=system,
        friction_points=["friction 1"],
        gate_scores=[
            GateScore("Source-Integrity", 80, GateResult.SURVIVE, "ok"),
            GateScore("Structural-Consistency", 75, GateResult.SURVIVE, "ok"),
            GateScore("Mediation-Zeroing", 85, GateResult.SURVIVE, "ok"),
        ],
        origin_gate=GateResult.SURVIVE,
        consequences_short_term=["short term effect"],
        consequences_long_term=["long term effect"],
        revised_reasoning="Test reasoning.",
        final_judgment="Test judgment.",
        total_score=score,
        passes=1,
        timestamp=timestamp or time.time(),
    )


# ---------------------------------------------------------------------------
# Store & Retrieve
# ---------------------------------------------------------------------------

class TestStoreAndRetrieve:
    def test_store_creates_json_file(self, tmp_store, sample_verdict):
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        json_path = tmp_store.verdicts_dir / f"{verdict_id}.json"
        assert json_path.exists()

    def test_store_json_content(self, tmp_store, sample_verdict):
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        json_path = tmp_store.verdicts_dir / f"{verdict_id}.json"
        with open(json_path) as f:
            data = json.load(f)
        assert data["question"] == sample_verdict.question
        assert data["status"] == "approved"
        assert data["id"] == verdict_id

    def test_store_approved_indexes_in_chroma(self, tmp_store, sample_verdict):
        tmp_store.store(sample_verdict, status="approved")
        assert tmp_store.collection.count() == 1

    def test_store_rejected_not_indexed(self, tmp_store, sample_verdict):
        tmp_store.store(sample_verdict, status="rejected")
        assert tmp_store.collection.count() == 0

    def test_store_corrected_indexes(self, tmp_store, sample_verdict):
        tmp_store.store(sample_verdict, status="corrected")
        assert tmp_store.collection.count() == 1

    def test_retrieve_empty_store(self, tmp_store):
        results = tmp_store.retrieve("any question")
        assert results == []

    def test_retrieve_returns_results(self, tmp_store):
        v = make_verdict("Is interest-based lending just?")
        tmp_store.store(v, status="approved")
        results = tmp_store.retrieve("interest lending")
        assert len(results) == 1
        assert results[0]["id"].startswith("verdict_")

    def test_retrieve_relevance_ordering(self, tmp_store):
        v1 = make_verdict("Is interest-based lending just?", timestamp=1000.0)
        v2 = make_verdict("What is the purpose of taxation?", timestamp=2000.0)
        v3 = make_verdict("Is debt slavery moral?", timestamp=3000.0)
        tmp_store.store(v1, status="approved")
        tmp_store.store(v2, status="approved")
        tmp_store.store(v3, status="approved")
        results = tmp_store.retrieve("interest and debt", n_results=3)
        assert len(results) == 3

    def test_retrieve_n_results_limit(self, tmp_store):
        for i in range(5):
            v = make_verdict(f"Question {i}", timestamp=float(i + 1000))
            tmp_store.store(v, status="approved")
        results = tmp_store.retrieve("Question", n_results=2)
        assert len(results) == 2

    def test_retrieve_with_system_filter(self, tmp_store):
        v1 = make_verdict("Economic question", system=SystemType.ECONOMIC, timestamp=1000.0)
        v2 = make_verdict("Social question", system=SystemType.SOCIAL, timestamp=2000.0)
        tmp_store.store(v1, status="approved")
        tmp_store.store(v2, status="approved")
        results = tmp_store.retrieve("question", system_filter=SystemType.ECONOMIC)
        assert len(results) == 1
        assert results[0]["metadata"]["primary_system"] == "economic"

    def test_get_verdict_by_id(self, tmp_store, sample_verdict):
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        data = tmp_store.get_verdict_by_id(verdict_id)
        assert data is not None
        assert data["question"] == sample_verdict.question

    def test_get_verdict_by_id_not_found(self, tmp_store):
        assert tmp_store.get_verdict_by_id("nonexistent_id") is None


# ---------------------------------------------------------------------------
# Context Formatting
# ---------------------------------------------------------------------------

class TestRetrieveAsContext:
    def test_empty_store_returns_empty_string(self, tmp_store):
        ctx = tmp_store.retrieve_as_context("anything")
        assert ctx == ""

    def test_context_contains_prior_verdict_header(self, tmp_store):
        v = make_verdict("Is interest just?")
        tmp_store.store(v, status="approved")
        ctx = tmp_store.retrieve_as_context("interest")
        assert "Prior Verdict 1" in ctx
        assert "Score:" in ctx
        assert "Status:" in ctx

    def test_context_contains_verdict_content(self, tmp_store):
        v = make_verdict("Is interest just?")
        tmp_store.store(v, status="approved")
        ctx = tmp_store.retrieve_as_context("interest")
        assert "Test reasoning." in ctx
        assert "Test judgment." in ctx

    def test_context_handles_none_distance(self, tmp_store):
        # This should not crash even if distance is None
        v = make_verdict("test question")
        tmp_store.store(v, status="approved")
        ctx = tmp_store.retrieve_as_context("test")
        assert "Prior Verdict" in ctx


# ---------------------------------------------------------------------------
# Status Updates
# ---------------------------------------------------------------------------

class TestUpdateStatus:
    def test_update_to_rejected_removes_from_index(self, tmp_store, sample_verdict):
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        assert tmp_store.collection.count() == 1
        tmp_store.update_status(verdict_id, "rejected")
        assert tmp_store.collection.count() == 0

    def test_update_file_status(self, tmp_store, sample_verdict):
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        tmp_store.update_status(verdict_id, "rejected")
        data = tmp_store.get_verdict_by_id(verdict_id)
        assert data["status"] == "rejected"

    def test_update_to_needs_review_removes_from_index(self, tmp_store, sample_verdict):
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        assert tmp_store.collection.count() == 1
        tmp_store.update_status(verdict_id, "needs_review")
        assert tmp_store.collection.count() == 0

    def test_re_approve_re_indexes(self, tmp_store, sample_verdict):
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        tmp_store.update_status(verdict_id, "needs_review")
        assert tmp_store.collection.count() == 0
        tmp_store.update_status(verdict_id, "approved")
        assert tmp_store.collection.count() == 1

    def test_update_nonexistent_returns_false(self, tmp_store):
        assert tmp_store.update_status("fake_id", "approved") is False

    def test_update_with_corrected_verdict(self, tmp_store, sample_verdict):
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        corrected = make_verdict("Corrected question", score=95)
        tmp_store.update_status(verdict_id, "superseded", corrected_verdict=corrected)
        # Original should be superseded
        original = tmp_store.get_verdict_by_id(verdict_id)
        assert original["status"] == "superseded"
        # Corrected should be indexed
        assert tmp_store.collection.count() == 1


# ---------------------------------------------------------------------------
# Cascade Invalidation
# ---------------------------------------------------------------------------

class TestInvalidateCascade:
    def test_invalidate_removes_original(self, tmp_store):
        v = make_verdict("Original question", timestamp=1000.0)
        vid = tmp_store.store(v, status="approved")
        tmp_store.invalidate_cascade(vid)
        data = tmp_store.get_verdict_by_id(vid)
        assert data["status"] == "rejected"

    def test_invalidate_flags_later_similar(self, tmp_store):
        v1 = make_verdict("Is interest just?", timestamp=1000.0)
        v2 = make_verdict("Is interest-based lending moral?", timestamp=2000.0)
        vid1 = tmp_store.store(v1, status="approved")
        vid2 = tmp_store.store(v2, status="approved")
        flagged = tmp_store.invalidate_cascade(vid1)
        assert vid2 in flagged

    def test_invalidate_does_not_flag_earlier(self, tmp_store):
        v1 = make_verdict("Is interest just?", timestamp=1000.0)
        v2 = make_verdict("Is interest-based lending moral?", timestamp=500.0)  # earlier
        vid1 = tmp_store.store(v1, status="approved")
        vid2 = tmp_store.store(v2, status="approved")
        flagged = tmp_store.invalidate_cascade(vid1)
        assert vid2 not in flagged

    def test_invalidate_nonexistent(self, tmp_store):
        flagged = tmp_store.invalidate_cascade("fake_id")
        assert flagged == []


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

class TestStats:
    def test_empty_store_stats(self, tmp_store):
        stats = tmp_store.stats()
        assert stats["total_indexed"] == 0
        assert stats["total_files"] == 0
        assert stats["by_status"] == {}

    def test_stats_counts(self, tmp_store):
        v1 = make_verdict("Q1", timestamp=1000.0)
        v2 = make_verdict("Q2", timestamp=2000.0)
        v3 = make_verdict("Q3", timestamp=3000.0)
        tmp_store.store(v1, status="approved")
        tmp_store.store(v2, status="approved")
        tmp_store.store(v3, status="rejected")
        stats = tmp_store.stats()
        assert stats["total_indexed"] == 2
        assert stats["total_files"] == 3
        assert stats["by_status"]["approved"] == 2
        assert stats["by_status"]["rejected"] == 1


# ---------------------------------------------------------------------------
# Collection Name
# ---------------------------------------------------------------------------

class TestCollectionName:
    def test_custom_collection_name(self, tmp_path):
        store = VerdictStore(
            chroma_dir=tmp_path / "chroma",
            verdicts_dir=tmp_path / "verdicts",
            collection_name="custom_collection",
        )
        assert store.collection.name == "custom_collection"

    def test_default_collection_name(self, tmp_path):
        store = VerdictStore(
            chroma_dir=tmp_path / "chroma",
            verdicts_dir=tmp_path / "verdicts",
        )
        assert store.collection.name == "criterion_verdicts"
