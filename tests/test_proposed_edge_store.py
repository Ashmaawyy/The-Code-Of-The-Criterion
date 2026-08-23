"""Tests for the ProposedEdgeStore."""

# pylint: disable=redefined-outer-name

import pytest

from al_furqan.kb.ingestion.models import ProposedEdge
from al_furqan.kb.ingestion.proposed_edge_store import ProposedEdgeStore


def _make_edge(**kwargs) -> ProposedEdge:
    """Create a test ProposedEdge with defaults."""
    defaults = {
        "id": ProposedEdge.generate_id(),
        "lesson_id": "lesson_01",
        "source_node": "6:1",
        "target_node": "توحيد",
        "edge_type": "discusses_topic",
        "provenance": "sheikh_ahmad_alsayed",
        "provenance_type": "scholarly_lecture",
        "reference": "مدارسة سورة الأنعام — الحلقة 01, 00:00 - 05:00",
        "timestamp_start": "0.0",
        "timestamp_end": "300.0",
        "transcript_chunk": "sample chunk text",
        "llm_reasoning": "Scholar explicitly discussed this topic",
        "llm_confidence": 0.85,
    }
    defaults.update(kwargs)
    return ProposedEdge(**defaults)


@pytest.fixture
def store(tmp_path):
    """Create a temporary store."""
    db_path = str(tmp_path / "test_edges.db")
    s = ProposedEdgeStore(db_path=db_path)
    yield s
    s.close()


class TestProposedEdgeStore:
    """TestProposedEdgeStore class."""

    def test_save_and_retrieve(self, store):
        """Save an edge and retrieve it by ID."""
        edge = _make_edge()
        store.save(edge)
        retrieved = store.get_by_id(edge.id)
        assert retrieved is not None
        assert retrieved.id == edge.id
        assert retrieved.source_node == "6:1"
        assert retrieved.target_node == "توحيد"

    def test_get_nonexistent(self, store):
        """Getting a nonexistent edge returns None."""
        assert store.get_by_id("nonexistent") is None

    def test_get_pending(self, store):
        """Get pending edges."""
        store.save(_make_edge(status="pending"))
        store.save(_make_edge(status="confirmed"))
        store.save(_make_edge(status="pending"))
        pending = store.get_pending()
        assert len(pending) == 2
        assert all(e.status == "pending" for e in pending)

    def test_get_pending_by_lesson(self, store):
        """Filter pending by lesson_id."""
        store.save(_make_edge(lesson_id="lesson_01", status="pending"))
        store.save(_make_edge(lesson_id="lesson_02", status="pending"))
        pending = store.get_pending(lesson_id="lesson_01")
        assert len(pending) == 1
        assert pending[0].lesson_id == "lesson_01"

    def test_confirm(self, store):
        """Confirm a pending edge."""
        edge = _make_edge()
        store.save(edge)
        result = store.confirm(edge.id, reviewed_by="mahmoud", notes="looks good")
        assert result is True
        updated = store.get_by_id(edge.id)
        assert updated.status == "confirmed"
        assert updated.reviewed_by == "mahmoud"
        assert updated.review_notes == "looks good"
        assert updated.review_timestamp > 0

    def test_reject(self, store):
        """Reject a pending edge."""
        edge = _make_edge()
        store.save(edge)
        result = store.reject(edge.id, reviewed_by="mahmoud", notes="inaccurate")
        assert result is True
        updated = store.get_by_id(edge.id)
        assert updated.status == "rejected"

    def test_edit_and_confirm(self, store):
        """Edit fields and confirm."""
        edge = _make_edge()
        store.save(edge)
        result = store.edit_and_confirm(
            edge.id,
            reviewed_by="mahmoud",
            notes="fixed source",
            source_node="6:2",
        )
        assert result is True
        updated = store.get_by_id(edge.id)
        assert updated.status == "edited"
        assert updated.source_node == "6:2"
        assert updated.target_node == "توحيد"  # unchanged

    def test_edit_nonexistent(self, store):
        """Editing a nonexistent edge returns False."""
        result = store.edit_and_confirm("nonexistent", reviewed_by="test")
        assert result is False

    def test_save_batch(self, store):
        """Save multiple edges at once."""
        edges = [_make_edge() for _ in range(5)]
        store.save_batch(edges)
        all_edges = store.get_all()
        assert len(all_edges) == 5

    def test_get_stats(self, store):
        """Get summary statistics."""
        store.save(_make_edge(status="pending", llm_confidence=0.8))
        store.save(_make_edge(status="pending", llm_confidence=0.9))
        store.save(_make_edge(status="confirmed", llm_confidence=0.7))
        stats = store.get_stats()
        assert stats["total"] == 3
        assert stats["pending"] == 2
        assert stats["confirmed"] == 1
        assert 0.7 < stats["avg_confidence"] < 0.9

    def test_get_rejection_patterns(self, store):
        """Analyze rejection patterns."""
        for _ in range(3):
            store.save(
                _make_edge(
                    status="rejected",
                    edge_type="discusses_topic",
                )
            )
            # We need to use reject to set review_notes
        edge1 = _make_edge()
        store.save(edge1)
        store.reject(edge1.id, "reviewer", "too speculative")
        edge2 = _make_edge()
        store.save(edge2)
        store.reject(edge2.id, "reviewer", "too speculative")

        patterns = store.get_rejection_patterns()
        assert len(patterns) >= 1

    def test_get_by_status(self, store):
        """Get edges by specific status."""
        store.save(_make_edge(status="pending"))
        store.save(_make_edge(status="rejected"))
        rejected = store.get_by_status("rejected")
        assert len(rejected) == 1
        assert rejected[0].status == "rejected"

    def test_confidence_preserved(self, store):
        """LLM confidence is preserved correctly."""
        edge = _make_edge(llm_confidence=0.923)
        store.save(edge)
        retrieved = store.get_by_id(edge.id)
        assert abs(retrieved.llm_confidence - 0.923) < 0.001
