"""Tests for the relationship extractor (with mocked LLM)."""

import json

from al_furqan.kb.ingestion.transcript_chunker import TranscriptChunk
from al_furqan.kb.ingestion.relationship_extractor import (
    extract_relationships,
    _parse_llm_response,
)
from al_furqan.providers.llm_layer import LLMProvider, LLMConfig


class MockLLM(LLMProvider):
    """Mock LLM that returns a canned JSON response."""

    def __init__(self, response: str):
        super().__init__(LLMConfig())
        self._response = response

    def generate(self, prompt: str) -> str:
        return self._response


def _make_chunk(text="sample text", start=0.0, end=60.0) -> TranscriptChunk:
    return TranscriptChunk(
        chunk_index=0,
        text=text,
        start_time=start,
        end_time=end,
        segment_indices=[0, 1, 2],
        word_count=len(text.split()),
    )


class TestParseResponse:
    """TestParseResponse class."""

    def test_valid_json(self):
        """Parse valid JSON response."""
        resp = json.dumps({
            "relationships": [{
                "source_node": "6:1", "target_node": "توحيد",
                "edge_type": "discusses_topic",
                "reasoning": "test", "confidence": 0.9,
            }],
            "verse_references": ["6:1"],
            "topics": ["توحيد"],
            "hadith_references": [],
        })
        parsed = _parse_llm_response(resp)
        assert len(parsed["relationships"]) == 1

    def test_json_in_code_fence(self):
        """Parse JSON wrapped in markdown code fences."""
        resp = (
            '```json\n{"relationships": [],'
            ' "verse_references": [], "topics": [],'
            ' "hadith_references": []}\n```'
        )
        parsed = _parse_llm_response(resp)
        assert parsed["relationships"] == []

    def test_garbage_returns_empty(self):
        """Garbage input returns empty result."""
        parsed = _parse_llm_response("this is not json at all")
        assert parsed["relationships"] == []

    def test_json_with_preamble(self):
        """JSON embedded in text."""
        resp = (
            'Here is the result:\n'
            '{"relationships": [{"source_node": "a",'
            ' "target_node": "b", "edge_type": "c",'
            ' "reasoning": "d", "confidence": 0.5}],'
            ' "verse_references": [], "topics": [],'
            ' "hadith_references": []}'
        )
        parsed = _parse_llm_response(resp)
        assert len(parsed["relationships"]) == 1


class TestExtractRelationships:
    """TestExtractRelationships class."""

    def test_basic_extraction(self):
        """Extract relationships from a chunk using mock LLM."""
        llm_response = json.dumps({
            "relationships": [
                {
                    "source_node": "6:1",
                    "target_node": "تحقيق العبودية",
                    "edge_type": "discusses_topic",
                    "reasoning": "الشيخ ذكر أن الموضوع الأكبر في السورة هو تحقيق العبودية",
                    "confidence": 0.95,
                },
                {
                    "source_node": "سورة الأنعام",
                    "target_node": "محاجة المشركين",
                    "edge_type": "connects_concept",
                    "reasoning": "الشيخ قال إن السورة من أهم المصادر في محاجة المشركين",
                    "confidence": 0.9,
                },
            ],
            "verse_references": ["6:1"],
            "topics": ["تحقيق العبودية", "محاجة المشركين"],
            "hadith_references": [],
        })

        llm = MockLLM(llm_response)
        chunk = _make_chunk("هذه السورة مدارها على تحقيق العبودية لله وحده")

        result = extract_relationships(chunk, llm, lesson_id="lesson_01")

        assert len(result.edges) == 2
        assert result.edges[0].source_node == "6:1"
        assert result.edges[0].status == "pending"
        assert result.edges[0].provenance == "sheikh_ahmad_alsayed"
        assert result.edges[0].lesson_id == "lesson_01"
        assert len(result.verse_references) == 1
        assert len(result.topics) == 2

    def test_empty_extraction(self):
        """Handle chunk with no extractable relationships."""
        llm_response = json.dumps({
            "relationships": [],
            "verse_references": [],
            "topics": [],
            "hadith_references": [],
        })
        llm = MockLLM(llm_response)
        chunk = _make_chunk("بسم الله الرحمن الرحيم")
        result = extract_relationships(chunk, llm)
        assert len(result.edges) == 0

    def test_malformed_relationship_skipped(self):
        """Malformed relationship entries are skipped."""
        llm_response = json.dumps({
            "relationships": [
                {"source_node": "", "target_node": "x", "edge_type": "y"},  # empty source
                {"source_node": "a", "target_node": "b", "edge_type": "c",
                 "reasoning": "r", "confidence": 0.8},  # valid
            ],
            "verse_references": [],
            "topics": [],
            "hadith_references": [],
        })
        llm = MockLLM(llm_response)
        chunk = _make_chunk()
        result = extract_relationships(chunk, llm)
        assert len(result.edges) == 1  # only the valid one

    def test_confidence_values(self):
        """Confidence values are properly stored."""
        llm_response = json.dumps({
            "relationships": [
                {"source_node": "6:50", "target_node": "غيب", "edge_type": "discusses_topic",
                 "reasoning": "explicit", "confidence": 0.72},
            ],
            "verse_references": ["6:50"],
            "topics": ["غيب"],
            "hadith_references": [],
        })
        llm = MockLLM(llm_response)
        result = extract_relationships(_make_chunk(), llm)
        assert abs(result.edges[0].llm_confidence - 0.72) < 0.01

    def test_reference_in_edge(self):
        """Edge includes lesson reference and timestamp."""
        llm_response = json.dumps({
            "relationships": [
                {"source_node": "a", "target_node": "b", "edge_type": "c",
                 "reasoning": "r", "confidence": 0.5},
            ],
            "verse_references": [], "topics": [], "hadith_references": [],
        })
        llm = MockLLM(llm_response)
        chunk = _make_chunk(start=60.0, end=120.0)
        result = extract_relationships(
            chunk, llm,
            lesson_reference="مدارسة سورة الأنعام — الحلقة 01",
        )
        assert "الحلقة 01" in result.edges[0].reference
        assert "01:00" in result.edges[0].reference
