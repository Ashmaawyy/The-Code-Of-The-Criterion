"""Tests for Tool Executor."""

# pylint: disable=redefined-outer-name

import os

import pytest

from al_furqan.kb.tafsir.kb_tools import TafsirKBTools
from al_furqan.kb.tafsir.tool_executor import (
    ToolExecutor,
    parse_tool_calls_from_response,
)

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "review", "proposed_edges.db"
)


@pytest.fixture
def executor():
    """Execute executor."""
    if not os.path.exists(DB_PATH):
        pytest.skip("proposed_edges.db not found")
    kb = TafsirKBTools(DB_PATH)
    return ToolExecutor(kb)


class TestToolExecution:
    """TestToolExecution class."""

    def test_search_by_verse(self, executor):
        """Test search_by_verse."""
        result = executor.execute("search_kb_by_verse", {"verse_ref": "6:5"})
        assert "نتائج البحث" in result
        assert "6:5" in result

    def test_search_by_topic(self, executor):
        """Test search_by_topic."""
        result = executor.execute("search_kb_by_topic", {"topic": "بدر"})
        assert "نتائج البحث" in result
        assert "بدر" in result

    def test_search_by_relation(self, executor):
        """Test search_by_relation."""
        result = executor.execute(
            "search_kb_by_relation",
            {"verse_ref": "6:5", "relation_type": "LINKED_HADITH"},
        )
        assert "LINKED_HADITH" in result

    def test_get_verse_context(self, executor):
        """Test get_verse_context."""
        result = executor.execute("get_verse_context", {"verse_ref": "6:5"})
        assert "سياق الآية" in result

    def test_unknown_tool(self, executor):
        """Test unknown_tool."""
        result = executor.execute("nonexistent_tool", {})
        assert "غير معروفة" in result

    def test_missing_args(self, executor):
        """Test missing_args."""
        result = executor.execute("search_kb_by_verse", {})
        assert "يجب تحديد" in result


class TestCallLog:
    """TestCallLog class."""

    def test_log_tracks_calls(self, executor):
        """Test log_tracks_calls."""
        executor.reset_log()
        executor.execute("search_kb_by_verse", {"verse_ref": "6:5"})
        executor.execute("search_kb_by_topic", {"topic": "بدر"})
        assert len(executor.call_log) == 2
        assert executor.call_log[0]["tool"] == "search_kb_by_verse"
        assert executor.call_log[1]["tool"] == "search_kb_by_topic"

    def test_log_reset(self, executor):
        """Test log_reset."""
        executor.execute("search_kb_by_verse", {"verse_ref": "6:5"})
        executor.reset_log()
        assert len(executor.call_log) == 0

    def test_log_tracks_success(self, executor):
        """Test log_tracks_success."""
        executor.reset_log()
        executor.execute("search_kb_by_verse", {"verse_ref": "6:5"})
        executor.execute("nonexistent", {})
        assert executor.call_log[0]["success"] is True
        assert executor.call_log[1]["success"] is False


class TestParseInlineToolCalls:
    """TestParseInlineToolCalls class."""

    def test_parse_search_by_verse(self):
        """Test parse_search_by_verse."""
        text = 'أحتاج أبحث: search_kb_by_verse("6:5") عن هذه الآية'
        calls = parse_tool_calls_from_response(text)
        assert len(calls) == 1
        assert calls[0]["name"] == "search_kb_by_verse"
        assert calls[0]["arguments"]["verse_ref"] == "6:5"

    def test_parse_search_by_topic(self):
        """Test parse_search_by_topic."""
        text = 'search_kb_by_topic("السنة الإلهية")'
        calls = parse_tool_calls_from_response(text)
        assert len(calls) == 1
        assert calls[0]["arguments"]["topic"] == "السنة الإلهية"

    def test_parse_multiple_calls(self):
        """Test parse_multiple_calls."""
        text = """
        search_kb_by_verse("6:5")
        search_kb_by_topic("بدر")
        """
        calls = parse_tool_calls_from_response(text)
        assert len(calls) == 2

    def test_no_calls(self):
        """Test no_calls."""
        text = "هذه إجابة عادية بدون أي tool calls"
        calls = parse_tool_calls_from_response(text)
        assert len(calls) == 0
