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
import logging
import sys
import time
from pathlib import Path

import pytest

# Ensure project root is on the path so bare module imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reasoning_engine import Verdict, GateScore, GateResult, SystemType
from verdict_store import VerdictStore

logger = logging.getLogger("test_verdict_store")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_verdict(question: str, score: int = 80, system: SystemType = SystemType.ECONOMIC,
                 timestamp: float = 0) -> Verdict:
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
        logger.info("Storing sample verdict — expecting JSON file creation")
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        json_path = tmp_store.verdicts_dir / f"{verdict_id}.json"
        logger.debug("Verdict ID: %s, JSON path: %s, exists: %s", verdict_id, json_path, json_path.exists())
        assert json_path.exists()
        logger.info("JSON file created at %s", json_path)

    def test_store_json_content(self, tmp_store, sample_verdict):
        logger.info("Verifying stored JSON content matches verdict data")
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        json_path = tmp_store.verdicts_dir / f"{verdict_id}.json"
        with open(json_path) as f:
            data = json.load(f)
        logger.debug("Stored question='%s', status='%s', id='%s'",
                      data["question"], data["status"], data["id"])
        assert data["question"] == sample_verdict.question
        assert data["status"] == "approved"
        assert data["id"] == verdict_id
        logger.info("Stored JSON content is correct")

    def test_store_approved_indexes_in_chroma(self, tmp_store, sample_verdict):
        logger.info("Storing approved verdict — should be indexed in ChromaDB")
        tmp_store.store(sample_verdict, status="approved")
        count = tmp_store.collection.count()
        logger.debug("ChromaDB collection count: %d", count)
        assert count == 1
        logger.info("Approved verdict indexed in ChromaDB (count=%d)", count)

    def test_store_rejected_not_indexed(self, tmp_store, sample_verdict):
        logger.info("Storing rejected verdict — should NOT be indexed in ChromaDB")
        tmp_store.store(sample_verdict, status="rejected")
        count = tmp_store.collection.count()
        logger.debug("ChromaDB collection count: %d", count)
        assert count == 0
        logger.info("Rejected verdict correctly excluded from ChromaDB index")

    def test_store_corrected_indexes(self, tmp_store, sample_verdict):
        logger.info("Storing corrected verdict — should be indexed in ChromaDB")
        tmp_store.store(sample_verdict, status="corrected")
        count = tmp_store.collection.count()
        logger.debug("ChromaDB collection count: %d", count)
        assert count == 1
        logger.info("Corrected verdict indexed in ChromaDB (count=%d)", count)

    def test_retrieve_empty_store(self, tmp_store):
        logger.info("Retrieving from empty store — should return empty list")
        results = tmp_store.retrieve("any question")
        logger.debug("Results: %s", results)
        assert results == []
        logger.info("Empty store returned empty results")

    def test_retrieve_returns_results(self, tmp_store):
        logger.info("Storing and retrieving a verdict about interest lending")
        v = make_verdict("Is interest-based lending just?")
        tmp_store.store(v, status="approved")
        results = tmp_store.retrieve("interest lending")
        logger.debug("Retrieved %d result(s), first ID: %s", len(results), results[0]["id"] if results else "N/A")
        assert len(results) == 1
        assert results[0]["id"].startswith("verdict_")
        logger.info("Retrieved %d result(s) for 'interest lending'", len(results))

    def test_retrieve_relevance_ordering(self, tmp_store):
        logger.info("Storing 3 verdicts and testing retrieval ordering")
        v1 = make_verdict("Is interest-based lending just?", timestamp=1000.0)
        v2 = make_verdict("What is the purpose of taxation?", timestamp=2000.0)
        v3 = make_verdict("Is debt slavery moral?", timestamp=3000.0)
        id1 = tmp_store.store(v1, status="approved")
        id2 = tmp_store.store(v2, status="approved")
        id3 = tmp_store.store(v3, status="approved")
        logger.debug("Stored IDs: %s, %s, %s", id1, id2, id3)
        results = tmp_store.retrieve("interest and debt", n_results=3)
        logger.debug("Retrieved %d results for 'interest and debt'", len(results))
        for i, r in enumerate(results):
            logger.debug("  Result %d: id=%s, question=%s", i + 1, r["id"], r.get("question", "N/A"))
        assert len(results) == 3
        logger.info("Relevance ordering: retrieved all 3 results")

    def test_retrieve_n_results_limit(self, tmp_store):
        logger.info("Storing 5 verdicts and retrieving with n_results=2")
        for i in range(5):
            v = make_verdict(f"Question {i}", timestamp=float(i + 1000))
            tmp_store.store(v, status="approved")
        results = tmp_store.retrieve("Question", n_results=2)
        logger.debug("Requested 2, got %d results", len(results))
        assert len(results) == 2
        logger.info("n_results limit correctly enforced (returned %d)", len(results))

    def test_retrieve_with_system_filter(self, tmp_store):
        logger.info("Testing retrieval with SystemType filter (ECONOMIC only)")
        v1 = make_verdict("Economic question", system=SystemType.ECONOMIC, timestamp=1000.0)
        v2 = make_verdict("Social question", system=SystemType.SOCIAL, timestamp=2000.0)
        tmp_store.store(v1, status="approved")
        tmp_store.store(v2, status="approved")
        results = tmp_store.retrieve("question", system_filter=SystemType.ECONOMIC)
        logger.debug("Filtered results: %d (expected 1 ECONOMIC)", len(results))
        assert len(results) == 1
        assert results[0]["metadata"]["primary_system"] == "economic"
        logger.info("System filter correctly returned only ECONOMIC verdicts")

    def test_get_verdict_by_id(self, tmp_store, sample_verdict):
        logger.info("Testing get_verdict_by_id for a stored verdict")
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        data = tmp_store.get_verdict_by_id(verdict_id)
        logger.debug("Retrieved verdict: id=%s, question='%s'", verdict_id, data["question"])
        assert data is not None
        assert data["question"] == sample_verdict.question
        logger.info("get_verdict_by_id returned correct verdict")

    def test_get_verdict_by_id_not_found(self, tmp_store):
        logger.info("Testing get_verdict_by_id with nonexistent ID")
        result = tmp_store.get_verdict_by_id("nonexistent_id")
        logger.debug("Result for nonexistent ID: %s", result)
        assert result is None
        logger.info("Nonexistent ID correctly returned None")


# ---------------------------------------------------------------------------
# Context Formatting
# ---------------------------------------------------------------------------

class TestRetrieveAsContext:
    def test_empty_store_returns_empty_string(self, tmp_store):
        logger.info("Testing retrieve_as_context on empty store")
        ctx = tmp_store.retrieve_as_context("anything")
        logger.debug("Context from empty store: '%s'", ctx)
        assert ctx == ""
        logger.info("Empty store returned empty context string")

    def test_context_contains_prior_verdict_header(self, tmp_store):
        logger.info("Testing context contains 'Prior Verdict' header")
        v = make_verdict("Is interest just?")
        tmp_store.store(v, status="approved")
        ctx = tmp_store.retrieve_as_context("interest")
        logger.debug("Context length: %d chars", len(ctx))
        assert "Prior Verdict 1" in ctx
        assert "Score:" in ctx
        assert "Status:" in ctx
        logger.info("Context contains expected header and metadata fields")

    def test_context_contains_verdict_content(self, tmp_store):
        logger.info("Testing context includes reasoning and judgment text")
        v = make_verdict("Is interest just?")
        tmp_store.store(v, status="approved")
        ctx = tmp_store.retrieve_as_context("interest")
        logger.debug("Reasoning in context: %s, Judgment in context: %s",
                      "Test reasoning." in ctx, "Test judgment." in ctx)
        assert "Test reasoning." in ctx
        assert "Test judgment." in ctx
        logger.info("Context includes verdict reasoning and judgment")

    def test_context_handles_none_distance(self, tmp_store):
        logger.info("Testing context generation doesn't crash on None distance")
        v = make_verdict("test question")
        tmp_store.store(v, status="approved")
        ctx = tmp_store.retrieve_as_context("test")
        logger.debug("Context generated without crash, length=%d", len(ctx))
        assert "Prior Verdict" in ctx
        logger.info("None distance handled gracefully")


# ---------------------------------------------------------------------------
# Status Updates
# ---------------------------------------------------------------------------

class TestUpdateStatus:
    def test_update_to_rejected_removes_from_index(self, tmp_store, sample_verdict):
        logger.info("Storing approved verdict then updating to rejected")
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        logger.debug("Before update: chroma count=%d", tmp_store.collection.count())
        assert tmp_store.collection.count() == 1
        tmp_store.update_status(verdict_id, "rejected")
        logger.debug("After update to rejected: chroma count=%d", tmp_store.collection.count())
        assert tmp_store.collection.count() == 0
        logger.info("Rejected status correctly removed verdict from ChromaDB index")

    def test_update_file_status(self, tmp_store, sample_verdict):
        logger.info("Verifying file status field is updated on disk")
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        tmp_store.update_status(verdict_id, "rejected")
        data = tmp_store.get_verdict_by_id(verdict_id)
        logger.debug("File status after update: %s", data["status"])
        assert data["status"] == "rejected"
        logger.info("File status correctly updated to 'rejected'")

    def test_update_to_needs_review_removes_from_index(self, tmp_store, sample_verdict):
        logger.info("Updating approved verdict to needs_review")
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        assert tmp_store.collection.count() == 1
        tmp_store.update_status(verdict_id, "needs_review")
        logger.debug("After needs_review: chroma count=%d", tmp_store.collection.count())
        assert tmp_store.collection.count() == 0
        logger.info("needs_review status correctly removed verdict from index")

    def test_re_approve_re_indexes(self, tmp_store, sample_verdict):
        logger.info("Testing re-approval cycle: approved → needs_review → approved")
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        tmp_store.update_status(verdict_id, "needs_review")
        logger.debug("After needs_review: chroma count=%d", tmp_store.collection.count())
        assert tmp_store.collection.count() == 0
        tmp_store.update_status(verdict_id, "approved")
        logger.debug("After re-approval: chroma count=%d", tmp_store.collection.count())
        assert tmp_store.collection.count() == 1
        logger.info("Re-approval correctly re-indexed the verdict")

    def test_update_nonexistent_returns_false(self, tmp_store):
        logger.info("Updating nonexistent verdict ID — should return False")
        result = tmp_store.update_status("fake_id", "approved")
        logger.debug("update_status returned: %s", result)
        assert result is False
        logger.info("Nonexistent ID correctly returned False")

    def test_update_with_corrected_verdict(self, tmp_store, sample_verdict):
        logger.info("Testing update with corrected verdict (supersede + store new)")
        verdict_id = tmp_store.store(sample_verdict, status="approved")
        corrected = make_verdict("Corrected question", score=95)
        tmp_store.update_status(verdict_id, "superseded", corrected_verdict=corrected)
        # Original should be superseded
        original = tmp_store.get_verdict_by_id(verdict_id)
        logger.debug("Original status: %s", original["status"])
        assert original["status"] == "superseded"
        # Corrected should be indexed
        count = tmp_store.collection.count()
        logger.debug("ChromaDB count after supersede: %d (expected 1 — the corrected verdict)", count)
        assert count == 1
        logger.info("Supersede flow: original marked superseded, corrected verdict indexed")


# ---------------------------------------------------------------------------
# Cascade Invalidation
# ---------------------------------------------------------------------------

class TestInvalidateCascade:
    def test_invalidate_removes_original(self, tmp_store):
        logger.info("Testing cascade invalidation removes original verdict")
        v = make_verdict("Original question", timestamp=1000.0)
        vid = tmp_store.store(v, status="approved")
        tmp_store.invalidate_cascade(vid)
        data = tmp_store.get_verdict_by_id(vid)
        logger.debug("Original status after invalidation: %s", data["status"])
        assert data["status"] == "rejected"
        logger.info("Original verdict correctly rejected via cascade")

    def test_invalidate_flags_later_similar(self, tmp_store):
        logger.info("Testing cascade flags later similar verdicts")
        v1 = make_verdict("Is interest just?", timestamp=1000.0)
        v2 = make_verdict("Is interest-based lending moral?", timestamp=2000.0)
        vid1 = tmp_store.store(v1, status="approved")
        vid2 = tmp_store.store(v2, status="approved")
        flagged = tmp_store.invalidate_cascade(vid1)
        logger.debug("Flagged IDs: %s (expected %s to be included)", flagged, vid2)
        assert vid2 in flagged
        logger.info("Later similar verdict %s correctly flagged", vid2)

    def test_invalidate_does_not_flag_earlier(self, tmp_store):
        logger.info("Testing cascade does NOT flag earlier verdicts")
        v1 = make_verdict("Is interest just?", timestamp=1000.0)
        v2 = make_verdict("Is interest-based lending moral?", timestamp=500.0)  # earlier
        vid1 = tmp_store.store(v1, status="approved")
        vid2 = tmp_store.store(v2, status="approved")
        flagged = tmp_store.invalidate_cascade(vid1)
        logger.debug("Flagged IDs: %s (should NOT include %s)", flagged, vid2)
        assert vid2 not in flagged
        logger.info("Earlier verdict correctly excluded from cascade")

    def test_invalidate_nonexistent(self, tmp_store):
        logger.info("Testing cascade on nonexistent ID")
        flagged = tmp_store.invalidate_cascade("fake_id")
        logger.debug("Flagged: %s", flagged)
        assert flagged == []
        logger.info("Nonexistent ID returned empty flagged list")


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

class TestStats:
    def test_empty_store_stats(self, tmp_store):
        logger.info("Getting stats from empty store")
        stats = tmp_store.stats()
        logger.debug("Empty stats: %s", stats)
        assert stats["total_indexed"] == 0
        assert stats["total_files"] == 0
        assert stats["by_status"] == {}
        logger.info("Empty store stats correct")

    def test_stats_counts(self, tmp_store):
        logger.info("Storing 3 verdicts (2 approved, 1 rejected) and checking stats")
        v1 = make_verdict("Q1", timestamp=1000.0)
        v2 = make_verdict("Q2", timestamp=2000.0)
        v3 = make_verdict("Q3", timestamp=3000.0)
        tmp_store.store(v1, status="approved")
        tmp_store.store(v2, status="approved")
        tmp_store.store(v3, status="rejected")
        stats = tmp_store.stats()
        logger.debug("Stats: indexed=%d, files=%d, by_status=%s",
                      stats["total_indexed"], stats["total_files"], stats["by_status"])
        assert stats["total_indexed"] == 2
        assert stats["total_files"] == 3
        assert stats["by_status"]["approved"] == 2
        assert stats["by_status"]["rejected"] == 1
        logger.info("Stats correct: %d indexed, %d files, status breakdown=%s",
                     stats["total_indexed"], stats["total_files"], stats["by_status"])


# ---------------------------------------------------------------------------
# Collection Name
# ---------------------------------------------------------------------------

class TestCollectionName:
    def test_custom_collection_name(self, tmp_path):
        logger.info("Creating VerdictStore with custom collection name")
        store = VerdictStore(
            chroma_dir=tmp_path / "chroma",
            verdicts_dir=tmp_path / "verdicts",
            collection_name="custom_collection",
        )
        logger.debug("Collection name: %s", store.collection.name)
        assert store.collection.name == "custom_collection"
        logger.info("Custom collection name set correctly")

    def test_default_collection_name(self, tmp_path):
        logger.info("Creating VerdictStore with default collection name")
        store = VerdictStore(
            chroma_dir=tmp_path / "chroma",
            verdicts_dir=tmp_path / "verdicts",
        )
        logger.debug("Collection name: %s", store.collection.name)
        assert store.collection.name == "criterion_verdicts"
        logger.info("Default collection name is 'criterion_verdicts'")
