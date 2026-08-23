"""Tests for the KB Tools."""

import os  # pylint: disable=wrong-import-order

import pytest

from al_furqan.kb.tafsir.kb_tools import TafsirKBTools

# pylint: disable=redefined-outer-name

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "review", "proposed_edges.db"
)


@pytest.fixture
def kb():
    """Execute kb."""
    if not os.path.exists(DB_PATH):
        pytest.skip("proposed_edges.db not found")
    return TafsirKBTools(DB_PATH)


class TestSearchByVerse:
    """TestSearchByVerse class."""

    def test_search_central_verse_6_1(self, kb):
        """Test search_central_verse_6_1."""
        results = kb.search_by_verse("6:1")
        assert len(results) > 0
        assert all(r.source_node == "6:1" or "6:1" in r.target_node for r in results)

    def test_search_central_verse_6_5(self, kb):
        """Test search_central_verse_6_5."""
        results = kb.search_by_verse("6:5")
        assert len(results) > 0
        # Should include entries where 6:5 is source (after our fix)
        source_entries = [r for r in results if r.source_node == "6:5"]
        assert len(source_entries) > 0

    def test_search_nonexistent_verse(self, kb):
        """Test search_nonexistent_verse."""
        results = kb.search_by_verse("99:999")
        assert len(results) == 0

    def test_results_have_confidence(self, kb):
        """Test results_have_confidence."""
        results = kb.search_by_verse("6:1")
        for r in results:
            assert 0.0 <= r.confidence <= 1.0


class TestSearchByTopic:
    """TestSearchByTopic class."""

    def test_search_badr(self, kb):
        """Test search_badr."""
        results = kb.search_by_topic("بدر")
        assert len(results) > 0

    def test_search_sunnah(self, kb):
        """Test search_sunnah."""
        results = kb.search_by_topic("السنة الإلهية")
        assert len(results) > 0

    def test_search_mushrikeen(self, kb):
        """Test search_mushrikeen."""
        results = kb.search_by_topic("المشركين")
        assert len(results) > 0

    def test_search_no_match(self, kb):
        """Test search_no_match."""
        results = kb.search_by_topic("xyznonexistent")
        assert len(results) == 0


class TestSearchByRelation:
    """TestSearchByRelation class."""

    def test_linked_hadith(self, kb):
        """Test linked_hadith."""
        results = kb.search_by_relation("6:5", "LINKED_HADITH")
        assert len(results) > 0
        assert all(r.edge_type == "LINKED_HADITH" for r in results)

    def test_linked_verse(self, kb):
        """Test linked_verse."""
        results = kb.search_by_relation("6:5", "LINKED_VERSE")
        assert len(results) > 0
        assert all(r.edge_type == "LINKED_VERSE" for r in results)

    def test_has_tafsir(self, kb):
        """Test has_tafsir."""
        results = kb.search_by_relation("6:5", "HAS_TAFSIR")
        assert len(results) > 0
        assert all(r.edge_type == "HAS_TAFSIR" for r in results)


class TestGetVerseContext:
    """TestGetVerseContext class."""

    def test_context_around_6_5(self, kb):
        """Test context_around_6_5."""
        ctx = kb.get_verse_context("6:5", verse_range=2)
        assert "center" in ctx
        assert ctx["center"] == "6:5"
        assert "entries" in ctx

    def test_invalid_ref(self, kb):
        """Test invalid_ref."""
        ctx = kb.get_verse_context("invalid")
        assert "error" in ctx


# pylint: disable=too-few-public-methods
class TestGetStats:
    """TestGetStats class."""

    def test_stats(self, kb):
        """Test stats."""
        stats = kb.get_stats()
        assert stats["total_entries"] == 67
        assert "6:1" in stats["central_verses"]
        assert "6:5" in stats["central_verses"]
        assert "HAS_TAFSIR" in stats["by_type"]


class TestToolDefinitions:
    """TestToolDefinitions class."""

    def test_tool_definitions_format(self):
        """Test tool_definitions_format."""
        tools = TafsirKBTools.get_tool_definitions()
        assert len(tools) == 4
        for tool in tools:
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]

    def test_tool_names(self):
        """Test tool_names."""
        tools = TafsirKBTools.get_tool_definitions()
        names = {t["function"]["name"] for t in tools}
        assert "search_kb_by_verse" in names
        assert "search_kb_by_topic" in names
        assert "search_kb_by_relation" in names
        assert "get_verse_context" in names


# pylint: disable=too-few-public-methods
class TestKBEntryFormat:
    """TestKBEntryFormat class."""

    def test_format_for_llm(self, kb):
        """Test format_for_llm."""
        results = kb.search_by_verse("6:5")
        assert len(results) > 0
        formatted = results[0].format_for_llm()
        assert "→" in formatted
        assert "الثقة" in formatted
        assert "التفسير" in formatted
