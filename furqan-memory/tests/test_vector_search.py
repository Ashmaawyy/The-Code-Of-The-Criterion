"""Tests for ChromaDB vector search layer."""

import pytest

from furqan_memory.storage.vector_store import MemoryVectorSearch

# pylint: disable=redefined-outer-name


@pytest.fixture
def vectors():
    """Create a fresh ephemeral vector store for each test."""
    return MemoryVectorSearch(persist_dir=None)


class TestVerdictVectors:
    """TestVerdictVectors class."""
    def test_add_and_search_verdict(self, vectors):
        """Test add_and_search_verdict."""
        vectors.add_verdict(
            "v_001",
            "Is interest (riba) permissible in Islam?",
            {"domain": "islamic"},
        )
        results = vectors.search_verdicts("riba interest banking", limit=5)
        assert len(results) >= 1
        assert results[0]["id"] == "v_001"
        assert results[0]["score"] > 0

    def test_search_empty_collection(self, vectors):
        """Test search_empty_collection."""
        results = vectors.search_verdicts("anything", limit=5)
        # ChromaDB with empty collection
        assert isinstance(results, list)

    def test_multiple_verdicts_relevance(self, vectors):  # pylint: disable=line-too-long
        """Test multiple_verdicts_relevance."""  # pylint: disable=line-too-long
        vectors.add_verdict("v_riba", "Is riba (interest) prohibited in Islam?", {"domain": "islamic"})
        vectors.add_verdict("v_fast", "What are the rules of fasting in Ramadan?", {"domain": "islamic"})
        vectors.add_verdict("v_zakat", "How to calculate zakat on gold?", {"domain": "islamic"})

        results = vectors.search_verdicts("interest banking loans riba", limit=3)
        assert len(results) == 3
        # The riba verdict should be most similar
        assert results[0]["id"] == "v_riba"

    def test_verdict_metadata_preserved(self, vectors):
        """Test verdict_metadata_preserved."""
        vectors.add_verdict("v_m", "Test question", {"domain": "islamic", "total_score": 85})
        results = vectors.search_verdicts("Test question", limit=1)
        assert results[0]["metadata"]["domain"] == "islamic"


class TestPatternVectors:
    """TestPatternVectors class."""
    def test_add_and_search_pattern(self, vectors):
        """Test add_and_search_pattern."""
        vectors.add_pattern(
            "p_001",
            "Interest-based transactions are prohibited",
            {"category": "fiqh"},
        )
        results = vectors.search_patterns("Is bank interest allowed?", limit=5)
        assert len(results) >= 1
        assert results[0]["id"] == "p_001"

    def test_search_empty_patterns(self, vectors):
        """Test search_empty_patterns."""
        results = vectors.search_patterns("anything", limit=5)
        assert results == []

    def test_multiple_patterns_ranking(self, vectors):  # pylint: disable=line-too-long
        """Test multiple_patterns_ranking."""  # pylint: disable=line-too-long
        vectors.add_pattern("p_riba", "Riba and interest-based lending is forbidden", {"category": "fiqh"})  # pylint: disable=line-too-long
        vectors.add_pattern("p_salah", "Prayer times and conditions for valid salah", {"category": "ibadah"})
        vectors.add_pattern("p_food", "Halal food preparation and slaughter requirements", {"category": "food"})

        results = vectors.search_patterns("Is taking a loan with interest permissible?", limit=3)
        assert results[0]["id"] == "p_riba"

    def test_pattern_metadata_preserved(self, vectors):
        """Test pattern_metadata_preserved."""
        vectors.add_pattern("p_m", "Test rule", {"category": "test", "confidence": 0.9})
        results = vectors.search_patterns("Test rule", limit=1)
        assert results[0]["metadata"]["category"] == "test"
