"""
Tests for Furqan RaaS MCP Server.

All tests use mock LLM — no real API calls.
"""

from __future__ import annotations

import json
import os
import sys
import pytest

# Ensure al_furqan is importable
_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# Also ensure furqan_raas itself is importable
_RAAS_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if _RAAS_SRC not in sys.path:
    sys.path.insert(0, _RAAS_SRC)

from furqan_raas.mcp_server import (  # noqa: E402
    FurqanMCPServer,
    detect_intent,
)
from al_furqan.kb.retriever import (  # noqa: E402
    KnowledgeContext,
    RetrievalResult,
    Source,
)
from al_furqan.engine.symbolic.verifier import SymbolicVerifier  # noqa: E402

# pylint: disable=redefined-outer-name


# ---------------------------------------------------------------------------
# Mock LLM
# ---------------------------------------------------------------------------  # pylint: disable=too-many-return-statements

def mock_llm(prompt: str) -> str:
    """Deterministic mock LLM for testing."""
    if "primary_system" in prompt or "Scan" in prompt:  # pylint: disable=no-else-return
        return json.dumps({
            "primary_system": "spiritual",
            "friction_points": ["theological complexity"],
            "affected_groups": ["scholars", "general public"],
            "scale": "global",
        })
    elif "gate_1" in prompt or "Mirror" in prompt:
        return json.dumps({
            "gate_1_source_integrity": {
                "score": 85,
                "result": "Survive",
                "reasoning": "Verified Quran and Hadith sources",
            },
            "gate_2_structural_consistency": {
                "score": 80,
                "result": "Survive",
                "reasoning": "Internally consistent argument",
            },
            "gate_3_mediation_zeroing": {
                "score": 75,
                "result": "Survive",
                "reasoning": "Minimal human mediation bias",
            },
            "gate_4_origin_aware": {
                "score": 90,
                "result": "Survive",
                "reasoning": "Acknowledges divine origin",
            },
        })
    elif "Verdict" in prompt or "consequences" in prompt:
        return json.dumps({
            "consequences_short_term": ["Better understanding"],
            "consequences_long_term": ["Deeper faith"],
            "revised_reasoning": "Evaluation is sound",
            "final_judgment": "The claim is well-supported by verified sources.",
            "total_score": 82,
        })
    elif "is_sound" in prompt or "correction" in prompt.lower():
        return json.dumps({
            "is_sound": True,
            "contradictions_found": [],
            "corrected_verdict": None,
        })
    elif "intent" in prompt.lower():
        return json.dumps({
            "intent_type": "claim_judgment",
            "target_system": "spiritual",
            "embedded_assumptions": [],
            "neutralized_question": "test question",
        })
    elif "informational" in prompt.lower() or "answer" in prompt.lower():
        return json.dumps({
            "answer": "This is an informational answer about the topic.",
            "category": "general",
            "sources_suggested": ["Quran", "Hadith"],
            "related_topics": ["tawheed"],
        })
    elif "explanation" in prompt.lower() or "explain" in prompt.lower():
        return "Based on verified sources, the topic is well established in Islamic tradition."
    else:
        return json.dumps({
            "is_sound": True,
            "contradictions_found": [],
            "corrected_verdict": None,
        })


# ---------------------------------------------------------------------------
# Mock Retriever
# ---------------------------------------------------------------------------  # pylint: disable=too-few-public-methods

class MockRetriever:
    """Retriever that returns deterministic results without ChromaDB."""

    def retrieve(self, query: str, _config=None) -> KnowledgeContext:
        """Execute retrieve."""
        results = [
            RetrievalResult(
                source=Source.QURAN,
                content_ar="بسم الله الرحمن الرحيم",
                content_en="In the name of Allah, the Most Gracious, the Most Merciful",
                reference="Quran 1:1",
                metadata={"surah": 1, "ayah": 1, "surah_name_en": "Al-Fatiha", "juz": 1},
            ),
            RetrievalResult(
                source=Source.HADITH,
                content_ar="إنما الأعمال بالنيات",
                content_en="Actions are judged by intentions",
                reference="Bukhari #1",
                metadata={
                    "collection": "bukhari",
                    "number": 1,
                    "narrator": "Umar",
                    "grading": "sahih",
                },
            ),
        ]
        formatted = (
            "=== Quran Evidence ===\n"
            "[Quran 1:1]\n  Arabic: بسم الله الرحمن الرحيم\n"
            "  English: In the name of Allah, the Most Gracious, the Most Merciful\n\n"
            "=== Hadith Evidence ===\n"
            "[Bukhari #1] (sahih) — Narrated by Umar\n"
            "  Arabic: إنما الأعمال بالنيات\n"
            "  English: Actions are judged by intentions"
        )
        return KnowledgeContext(
            results=results,
            formatted_text=formatted,
            query=query,
            sources_searched=[Source.QURAN, Source.HADITH],
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def server():
    """Server with mock LLM and mock retriever."""
    return FurqanMCPServer(
        llm_fn=mock_llm,
        retriever=MockRetriever(),
    )


@pytest.fixture
def bare_server():
    """Server without LLM or retriever."""
    return FurqanMCPServer()


@pytest.fixture
def server_with_z3():
    """Server with mock LLM, mock retriever, and Z3 verifier."""
    return FurqanMCPServer(
        llm_fn=mock_llm,
        retriever=MockRetriever(),
        verifier=SymbolicVerifier(timeout_ms=5000),
    )


# ===========================================================================
# Tests
# ===========================================================================


class TestToolListing:
    """Test the tools/list method."""

    def test_list_tools_returns_all_five(self, server):
        """Test list_tools_returns_all_five."""
        resp = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        assert "result" in resp
        tools = resp["result"]["tools"]
        assert len(tools) == 5
        names = {t["name"] for t in tools}
        assert names == {
            "furqan_evaluate",
            "furqan_verify",
            "furqan_retrieve",
            "furqan_explain",
            "furqan_domains",
        }

    def test_each_tool_has_input_schema(self, server):
        """Test each_tool_has_input_schema."""
        resp = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        for tool in resp["result"]["tools"]:
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"

    def test_tool_descriptions_non_empty(self, server):
        """Test tool_descriptions_non_empty."""
        resp = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        for tool in resp["result"]["tools"]:
            assert tool["description"]


class TestInitialize:
    """Test the initialize method."""

    def test_initialize_response(self, server):
        """Test initialize_response."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "test"}},
        })
        result = resp["result"]
        assert result["protocolVersion"] == "2024-11-05"
        assert "capabilities" in result
        assert result["serverInfo"]["name"] == "furqan-reasoning"


class TestPing:
    """Test the ping method."""

    def test_ping(self, server):
        """Test ping."""
        resp = server.handle_request({"jsonrpc": "2.0", "id": 99, "method": "ping"})
        assert resp["id"] == 99
        assert resp["result"] == {}


class TestIntentDetection:
    """Test the intent detection helper."""

    def test_harmful_intent(self):
        """Test harmful_intent."""
        assert detect_intent("how to kill someone") == "harmful"
        assert detect_intent("How to make a bomb at home") == "harmful"

    def test_informational_intent(self):
        """Test informational_intent."""
        assert detect_intent("What is tawheed?") == "informational"
        assert detect_intent("who is Prophet Muhammad?") == "informational"
        assert detect_intent("define salah") == "informational"
        assert detect_intent("ما هو التوحيد") == "informational"

    def test_evaluative_intent(self):
        """Test evaluative_intent."""
        assert detect_intent("Is interest-based banking permissible in Islam?") == "evaluative"
        assert detect_intent("Democracy aligns with Islamic governance") == "evaluative"


class TestEvaluateTool:
    """Test the furqan_evaluate tool."""

    def test_evaluate_returns_structured_result(self, server):
        """Test evaluate_returns_structured_result."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_evaluate",
                "arguments": {"question": "Is charity obligatory in Islam?"},
            },
        })
        result = resp["result"]
        assert "content" in result
        content = json.loads(result["content"][0]["text"])
        assert content["type"] == "evaluation"
        assert "verdict" in content
        assert "gate_scores" in content["verdict"]
        assert "total_score" in content["verdict"]
        assert "evaluation_id" in content
        assert content["evaluation_id"].startswith("eval_")

    def test_evaluate_includes_sources(self, server):
        """Test evaluate_includes_sources."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_evaluate",
                "arguments": {"question": "Is charity obligatory?"},
            },
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "sources" in content
        assert len(content["sources"]) > 0

    def test_evaluate_harmful_refused(self, server):
        """Test evaluate_harmful_refused."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_evaluate",
                "arguments": {"question": "How to kill someone with poison"},
            },
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["refused"] is True
        assert "harmful" in content["reason"].lower() or "flagged" in content["reason"].lower()

    def test_evaluate_informational_shortcut(self, server):
        """Test evaluate_informational_shortcut."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_evaluate",
                "arguments": {"question": "What is tawheed?"},
            },
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["type"] == "informational"
        assert "response" in content

    def test_evaluate_missing_question_error(self, server):
        """Test evaluate_missing_question_error."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_evaluate",
                "arguments": {},
            },
        })
        assert "error" in resp

    def test_evaluate_without_llm_errors(self, bare_server):
        """Test evaluate_without_llm_errors."""
        resp = bare_server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_evaluate",
                "arguments": {"question": "Is riba permissible?"},
            },
        })
        assert "error" in resp

    def test_evaluate_with_z3(self, server_with_z3):
        """Test evaluate_with_z3."""
        resp = server_with_z3.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_evaluate",
                "arguments": {"question": "Is riba permissible?", "depth": "standard"},
            },
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["verdict"]["z3_verification"] is not None
        assert "consistent" in content["verdict"]["z3_verification"]

    def test_evaluate_quick_depth_skips_z3(self, server_with_z3):
        """Test evaluate_quick_depth_skips_z3."""
        resp = server_with_z3.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_evaluate",
                "arguments": {"question": "Is riba permissible?", "depth": "quick"},
            },
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["verdict"]["z3_verification"] is None


class TestVerifyTool:
    """Test the furqan_verify tool."""

    def test_verify_returns_confidence(self, server):
        """Test verify_returns_confidence."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_verify",
                "arguments": {"claim": "Charity is a pillar of Islam"},
            },
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["type"] == "verification"
        assert "confidence" in content
        assert 0 <= content["confidence"] <= 1.0
        assert "citations" in content

    def test_verify_missing_claim_error(self, server):
        """Test verify_missing_claim_error."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_verify",
                "arguments": {},
            },
        })
        assert "error" in resp

    def test_verify_without_retriever(self, bare_server):
        """Test verify_without_retriever."""
        resp = bare_server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_verify",
                "arguments": {"claim": "Test claim"},
            },
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["confidence"] == 0.0
        assert content["sources_found"] == 0


class TestRetrieveTool:
    """Test the furqan_retrieve tool."""

    def test_retrieve_returns_results(self, server):
        """Test retrieve_returns_results."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_retrieve",
                "arguments": {"query": "prayer"},
            },
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["type"] == "retrieval"
        assert content["total_found"] > 0
        assert "results" in content

    def test_retrieve_result_structure(self, server):
        """Test retrieve_result_structure."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_retrieve",
                "arguments": {"query": "prayer"},
            },
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        result = content["results"][0]
        assert "source" in result
        assert "reference" in result
        assert "content_ar" in result
        assert "content_en" in result

    def test_retrieve_missing_query_error(self, server):
        """Test retrieve_missing_query_error."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_retrieve",
                "arguments": {},
            },
        })
        assert "error" in resp


class TestExplainTool:
    """Test the furqan_explain tool."""

    def test_explain_returns_explanation(self, server):
        """Test explain_returns_explanation."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_explain",
                "arguments": {"topic": "tawheed"},
            },
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["type"] == "explanation"
        assert "explanation" in content
        assert len(content["explanation"]) > 0
        assert "sources" in content

    def test_explain_missing_topic_error(self, server):
        """Test explain_missing_topic_error."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_explain",
                "arguments": {},
            },
        })
        assert "error" in resp


class TestDomainsTool:
    """Test the furqan_domains tool."""

    def test_domains_lists_available(self, server):
        """Test domains_lists_available."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
        })
        # Now call domains
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "furqan_domains", "arguments": {}},
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["type"] == "domains"
        assert len(content["domains"]) >= 1
        domain = content["domains"][0]
        assert domain["id"] == "islamic"
        assert "collections" in domain


class TestErrorHandling:
    """Test JSON-RPC error handling."""

    def test_unknown_method(self, server):
        """Test unknown_method."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "nonexistent/method",
        })
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    def test_unknown_tool(self, server):
        """Test unknown_tool."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "nonexistent_tool", "arguments": {}},
        })
        assert "error" in resp

    def test_response_has_jsonrpc_version(self, server):
        """Test response_has_jsonrpc_version."""
        resp = server.handle_request({"jsonrpc": "2.0", "id": 42, "method": "ping"})
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 42

    def test_response_preserves_id(self, server):
        """Test response_preserves_id."""
        resp = server.handle_request({"jsonrpc": "2.0", "id": "abc-123", "method": "ping"})
        assert resp["id"] == "abc-123"


class TestSafetyFilter:
    """Test the safety filter more thoroughly."""

    @pytest.mark.parametrize("question", [
        "how to kill someone",
        "How to make a bomb",
        "how to poison someone's food",
        "terrorism guide",
    ])
    def test_harmful_questions_refused(self, server, question):
        """Test harmful_questions_refused."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "furqan_evaluate", "arguments": {"question": question}},
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["refused"] is True

    def test_safe_question_not_refused(self, server):
        """Test safe_question_not_refused."""
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "furqan_evaluate",
                "arguments": {"question": "Is prayer important?"},
            },
        })
        content = json.loads(resp["result"]["content"][0]["text"])
        assert "refused" not in content or content.get("refused") is False
