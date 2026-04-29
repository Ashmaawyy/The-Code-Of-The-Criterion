"""Tests for MCP Memory Server — JSON-RPC protocol tests."""

import json

import pytest

from furqan_memory.storage.sqlite_store import MemoryStore
from furqan_memory.storage.vector_store import MemoryVectorSearch
from furqan_memory.memory_manager import MemoryManager
from furqan_memory.mcp_server import FurqanMemoryMCPServer

# pylint: disable=redefined-outer-name


@pytest.fixture
def server(tmp_path):
    """Create a fresh MCP server for each test."""
    store = MemoryStore(str(tmp_path / "test.db"))
    vectors = MemoryVectorSearch(persist_dir=None)
    manager = MemoryManager(store, vectors)
    srv = FurqanMemoryMCPServer(manager=manager)
    yield srv
    store.close()


def _rpc(server, method, params=None, req_id=1):
    """Helper to make a JSON-RPC request."""
    request = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}
    return server.handle_request(request)


def _tool_call(server, tool_name, arguments=None, req_id=1):
    """Helper to call a tool via JSON-RPC."""
    return _rpc(server, "tools/call", {"name": tool_name, "arguments": arguments or {}}, req_id)


def _parse_content(response):
    """Extract the parsed content from a tool response."""
    result = response["result"]
    text = result["content"][0]["text"]
    return json.loads(text)


class TestProtocol:
    """TestProtocol class."""
    def test_initialize(self, server):
        """Test initialize."""
        resp = _rpc(server, "initialize")
        assert resp["result"]["protocolVersion"] == "2024-11-05"
        assert resp["result"]["serverInfo"]["name"] == "furqan-memory"

    def test_tool_listing(self, server):
        """Test tool_listing."""
        resp = _rpc(server, "tools/list")
        tools = resp["result"]["tools"]
        names = [t["name"] for t in tools]
        assert "furqan_remember" in names
        assert "furqan_recall" in names
        assert "furqan_recognize" in names
        assert "furqan_feedback" in names
        assert "furqan_memory_stats" in names
        assert len(tools) == 5

    def test_ping(self, server):
        """Test ping."""
        resp = _rpc(server, "ping")
        assert resp["result"] == {}

    def test_unknown_method(self, server):
        """Test unknown_method."""
        resp = _rpc(server, "nonexistent/method")
        assert "error" in resp
        assert resp["error"]["code"] == -32601


class TestRememberTool:
    """TestRememberTool class."""
    def test_remember_success(self, server):
        """Test remember_success."""
        resp = _tool_call(server, "furqan_remember", {
            "question": "Is charity obligatory?",
            "verdict": {"total_score": 85, "final_judgment": "Yes"},
        })
        content = _parse_content(resp)
        assert content["type"] == "remembered"
        assert content["verdict_id"].startswith("v_")

    def test_remember_missing_question(self, server):
        """Test remember_missing_question."""
        resp = _tool_call(server, "furqan_remember", {"verdict": {"score": 1}})
        assert "error" in resp

    def test_remember_missing_verdict(self, server):
        """Test remember_missing_verdict."""
        resp = _tool_call(server, "furqan_remember", {"question": "test?"})
        assert "error" in resp


class TestRecallTool:
    """TestRecallTool class."""
    def test_recall_after_remember(self, server):
        """Test recall_after_remember."""
        _tool_call(server, "furqan_remember", {
            "question": "Is riba haram?",
            "verdict": {"total_score": 95},
        })
        resp = _tool_call(server, "furqan_recall", {"query": "riba interest"})
        content = _parse_content(resp)
        assert content["type"] == "recall"
        assert content["total_found"] >= 1

    def test_recall_empty(self, server):
        """Test recall_empty."""
        resp = _tool_call(server, "furqan_recall", {"query": "anything"})
        content = _parse_content(resp)
        assert content["total_found"] == 0

    def test_recall_missing_query(self, server):
        """Test recall_missing_query."""
        resp = _tool_call(server, "furqan_recall", {})
        assert "error" in resp


class TestRecognizeTool:
    """TestRecognizeTool class."""
    def test_recognize_no_match(self, server):
        """Test recognize_no_match."""
        resp = _tool_call(server, "furqan_recognize", {"query": "random question"})
        content = _parse_content(resp)
        assert content["type"] == "recognized"
        assert content["matched"] is False

    def test_recognize_missing_query(self, server):
        """Test recognize_missing_query."""
        resp = _tool_call(server, "furqan_recognize", {})
        assert "error" in resp


class TestStatsTool:
    """TestStatsTool class."""
    def test_stats_empty(self, server):
        """Test stats_empty."""
        resp = _tool_call(server, "furqan_memory_stats", {})
        content = _parse_content(resp)
        assert content["type"] == "stats"
        assert content["verdicts"] == 0

    def test_stats_after_operations(self, server):
        """Test stats_after_operations."""
        _tool_call(server, "furqan_remember", {
            "question": "Test?", "verdict": {"total_score": 80},
        })
        resp = _tool_call(server, "furqan_memory_stats", {})
        content = _parse_content(resp)
        assert content["verdicts"] == 1
        assert content["vector_verdicts"] == 1


class TestFeedbackTool:
    """TestFeedbackTool class."""
    def test_feedback_success(self, server):
        """Test feedback_success."""
        # First remember something
        r = _tool_call(server, "furqan_remember", {
            "question": "Test?", "verdict": {"total_score": 80},
        })
        vid = _parse_content(r)["verdict_id"]

        resp = _tool_call(server, "furqan_feedback", {
            "verdict_id": vid, "rating": "positive",
        })
        content = _parse_content(resp)
        assert content["type"] == "feedback"
        assert content["feedback_id"].startswith("f_")

    def test_feedback_invalid_rating(self, server):
        """Test feedback_invalid_rating."""
        resp = _tool_call(server, "furqan_feedback", {
            "verdict_id": "v_xxx", "rating": "invalid",
        })
        assert "error" in resp
