"""Tests for the Tafsir Pipeline (end-to-end with mock LLM)."""

# pylint: disable=redefined-outer-name

import os

import pytest
from al_furqan.engine.tafsir.pipeline import TafsirPipeline, PipelineResult
from al_furqan.kb.tafsir.query_analyzer import QueryType

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "review", "proposed_edges.db")


def mock_llm_no_tools(_messages, _tools=None):
    """Mock LLM that answers directly without using tools."""
    return {
        "content": "هذه إجابة مباشرة عن سورة الأنعام.",
        "tool_calls": None,
    }


def mock_llm_with_tool_call(messages, _tools=None):
    """Mock LLM that makes one tool call then answers."""
    # First call: make a tool call
    if len(messages) <= 2:
        return {
            "content": "",
            "tool_calls": [{
                "id": "call_1",
                "function": {
                    "name": "search_kb_by_verse",
                    "arguments": '{"verse_ref": "6:5"}'
                }
            }],
        }
    # Second call: answer with tool results
    return {
        "content": "بناءً على قاعدة المعرفة، الآية 6:5 مرتبطة بيوم بدر.",
        "tool_calls": None,
    }


def mock_llm_inline_tools(messages, _tools=None):
    """Mock LLM that uses inline tool calls (text-based)."""
    if len(messages) <= 2:
        return {
            "content": 'أحتاج أبحث أولاً: search_kb_by_verse("6:5")',
            "tool_calls": None,
        }
    return {
        "content": "وجدت أن الآية مرتبطة بيوم بدر حسب الشيخ أحمد السيد.",
        "tool_calls": None,
    }


@pytest.fixture
def pipeline_no_tools():
    """Execute pipeline_no_tools."""
    if not os.path.exists(DB_PATH):
        pytest.skip("proposed_edges.db not found")
    return TafsirPipeline(DB_PATH, mock_llm_no_tools, model_name="mock-no-tools")


@pytest.fixture
def pipeline_with_tools():
    """Execute pipeline_with_tools."""
    if not os.path.exists(DB_PATH):
        pytest.skip("proposed_edges.db not found")
    return TafsirPipeline(DB_PATH, mock_llm_with_tool_call, model_name="mock-with-tools")


@pytest.fixture
def pipeline_inline():
    """Execute pipeline_inline."""
    if not os.path.exists(DB_PATH):
        pytest.skip("proposed_edges.db not found")
    return TafsirPipeline(DB_PATH, mock_llm_inline_tools, model_name="mock-inline")


class TestPipelineBasic:
    """TestPipelineBasic class."""
    def test_returns_result(self, pipeline_no_tools):
        """Test returns_result."""
        result = pipeline_no_tools.run("ما تفسير الآية 6:5؟")
        assert isinstance(result, PipelineResult)
        assert result.llm_response != ""

    def test_query_analysis(self, pipeline_no_tools):
        """Test query_analysis."""
        result = pipeline_no_tools.run("ما تفسير الآية 6:5؟")
        assert "6:5" in result.query_analysis.verse_refs
        assert result.query_analysis.query_type == QueryType.TAFSIR

    def test_reasoning_plan(self, pipeline_no_tools):
        """Test reasoning_plan."""
        result = pipeline_no_tools.run("إيه علاقة أول أربع آيات بالآية 5")
        assert result.reasoning_plan.template_name == "ربط بين آيات"
        assert "Axioms" in result.reasoning_plan.system_prompt

    def test_metadata(self, pipeline_no_tools):
        """Test metadata."""
        result = pipeline_no_tools.run("ما تفسير الآية 6:5؟")
        assert result.total_time_ms > 0
        assert result.llm_calls >= 1
        assert result.model == "mock-no-tools"


class TestPipelineWithTools:
    """TestPipelineWithTools class."""
    def test_tool_calls_executed(self, pipeline_with_tools):
        """Test tool_calls_executed."""
        result = pipeline_with_tools.run("ما تفسير الآية 6:5؟")
        assert len(result.tool_calls) > 0
        assert result.tool_calls[0]["name"] == "search_kb_by_verse"

    def test_tool_results_stored(self, pipeline_with_tools):
        """Test tool_results_stored."""
        result = pipeline_with_tools.run("ما تفسير الآية 6:5؟")
        assert len(result.tool_results) > 0

    def test_final_response_uses_tools(self, pipeline_with_tools):
        """Test final_response_uses_tools."""
        result = pipeline_with_tools.run("ما تفسير الآية 6:5؟")
        assert "بدر" in result.llm_response

    def test_multiple_llm_calls(self, pipeline_with_tools):
        """Test multiple_llm_calls."""
        result = pipeline_with_tools.run("ما تفسير الآية 6:5؟")
        assert result.llm_calls >= 2  # First call = tool, second = answer


class TestPipelineInlineTools:
    """TestPipelineInlineTools class."""
    def test_inline_tool_detection(self, pipeline_inline):
        """Test inline_tool_detection."""
        result = pipeline_inline.run("ما تفسير الآية 6:5؟")
        assert len(result.tool_calls) > 0

    def test_inline_tool_results(self, pipeline_inline):
        """Test inline_tool_results."""
        result = pipeline_inline.run("ما تفسير الآية 6:5؟")
        assert "الشيخ أحمد السيد" in result.llm_response  # pylint: disable=too-few-public-methods


# pylint: disable=too-few-public-methods
class TestPipelineSummary:
    """TestPipelineSummary class."""
    def test_summary_format(self, pipeline_no_tools):
        """Test summary_format."""
        result = pipeline_no_tools.run("ما تفسير الآية 6:5؟")
        summary = result.summary()
        assert "Question:" in summary
        assert "Type:" in summary
        assert "Template:" in summary
        assert "Tool calls:" in summary


class TestPipelineEdgeCases:
    """TestPipelineEdgeCases class."""
    def test_empty_question(self, pipeline_no_tools):
        """Test empty_question."""
        result = pipeline_no_tools.run("")
        assert isinstance(result, PipelineResult)

    def test_general_question(self, pipeline_no_tools):
        """Test general_question."""
        result = pipeline_no_tools.run("ما هو الإسلام؟")
        assert result.reasoning_plan.template_name == "سؤال عام"
