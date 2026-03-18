"""
Unit tests for reasoning_engine.py

Tests:
- Data structures (SystemType, GateResult, GateScore, Verdict)
- Serialization / deserialization (to_dict, from_dict, to_log)
- Prompt builders
- JSON parsing from LLM responses
- Full evaluation pipeline with mock LLM
- Self-correction loop behavior
"""

import json
import time

import pytest

from reasoning_engine import (
    SystemType,
    GateResult,
    GateScore,
    Verdict,
    ReasoningEngine,
    build_scan_prompt,
    build_mirror_prompt,
    build_verdict_prompt,
    build_correction_prompt,
)
from conftest import (
    make_mock_llm,
    MOCK_SCAN_RESPONSE,
    MOCK_MIRROR_RESPONSE,
    MOCK_VERDICT_RESPONSE,
    MOCK_CORRECTION_SOUND,
    MOCK_CORRECTION_WITH_FIX,
)


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

class TestSystemType:
    def test_all_values(self):
        expected = {"economic", "social", "spiritual", "political",
                    "legal", "technological", "environmental", "mixed"}
        assert {e.value for e in SystemType} == expected

    def test_from_string(self):
        assert SystemType("economic") == SystemType.ECONOMIC
        assert SystemType("mixed") == SystemType.MIXED

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            SystemType("nonexistent")


class TestGateResult:
    def test_values(self):
        assert GateResult.SURVIVE.value == "Survive"
        assert GateResult.FAIL.value == "Fail"


class TestGateScore:
    def test_to_dict(self):
        gs = GateScore("Source-Integrity", 85, GateResult.SURVIVE, "Solid data.")
        d = gs.to_dict()
        assert d == {
            "name": "Source-Integrity",
            "score": 85,
            "result": "Survive",
            "reasoning": "Solid data.",
        }

    def test_fail_result(self):
        gs = GateScore("Test", 30, GateResult.FAIL, "Weak.")
        assert gs.result == GateResult.FAIL
        assert gs.to_dict()["result"] == "Fail"


class TestVerdict:
    def test_to_dict(self, sample_verdict):
        d = sample_verdict.to_dict()
        assert d["question"] == "Is interest-based lending just?"
        assert d["primary_system"] == "economic"
        assert d["total_score"] == 85
        assert d["origin_gate"] == "Survive"
        assert len(d["gate_scores"]) == 3
        assert d["gate_scores"][0]["name"] == "Source-Integrity"

    def test_to_log(self, sample_verdict):
        log = sample_verdict.to_log()
        assert "Question: Is interest-based lending just?" in log
        assert "Primary System Identified: economic" in log
        assert "Source-Integrity: 85/100 [Survive]" in log
        assert "Origin-Aware Gate: Survive" in log
        assert "Total Score: 85" in log

    def test_from_dict_roundtrip(self, sample_verdict):
        d = sample_verdict.to_dict()
        rebuilt = Verdict.from_dict(d)
        assert rebuilt.question == sample_verdict.question
        assert rebuilt.primary_system == sample_verdict.primary_system
        assert rebuilt.total_score == sample_verdict.total_score
        assert rebuilt.origin_gate == sample_verdict.origin_gate
        assert rebuilt.passes == sample_verdict.passes
        assert len(rebuilt.gate_scores) == len(sample_verdict.gate_scores)
        for original, restored in zip(sample_verdict.gate_scores, rebuilt.gate_scores):
            assert original.name == restored.name
            assert original.score == restored.score
            assert original.result == restored.result

    def test_from_dict_defaults(self):
        v = Verdict.from_dict({})
        assert v.question == ""
        assert v.primary_system == SystemType.MIXED
        assert v.total_score == 0
        assert v.gate_scores == []
        assert v.origin_gate == GateResult.FAIL

    def test_from_dict_invalid_system_type(self):
        v = Verdict.from_dict({"primary_system": "invalid_system"})
        assert v.primary_system == SystemType.MIXED

    def test_from_dict_string_score(self):
        v = Verdict.from_dict({"total_score": "85"})
        assert v.total_score == 85
        assert isinstance(v.total_score, int)

    def test_timestamp_auto_set(self):
        before = time.time()
        v = Verdict(
            question="test", primary_system=SystemType.MIXED,
            friction_points=[], gate_scores=[], origin_gate=GateResult.FAIL,
            consequences_short_term=[], consequences_long_term=[],
            revised_reasoning="", final_judgment="", total_score=0, passes=0,
        )
        after = time.time()
        assert before <= v.timestamp <= after


# ---------------------------------------------------------------------------
# Prompt Builders
# ---------------------------------------------------------------------------

class TestPromptBuilders:
    def test_scan_prompt_contains_question(self):
        prompt = build_scan_prompt("Is democracy effective?")
        assert "Is democracy effective?" in prompt
        assert "THE SCAN" in prompt
        assert "TRANSCENDENCE NECESSITY PROOF" in prompt

    def test_scan_prompt_with_context(self):
        prompt = build_scan_prompt("test question", context="prior verdict info")
        assert "prior verdict info" in prompt
        assert "Relevant prior verdicts" in prompt

    def test_scan_prompt_without_context(self):
        prompt = build_scan_prompt("test question", context="")
        assert "Relevant prior verdicts" not in prompt

    def test_mirror_prompt_contains_scan_result(self):
        scan = {"primary_system": "social", "friction_points": ["fp1"]}
        prompt = build_mirror_prompt("test", scan)
        assert "THE MIRROR" in prompt
        assert '"primary_system": "social"' in prompt
        assert "TRI-AXIAL SURVIVAL GATES" in prompt

    def test_verdict_prompt_contains_both_results(self):
        scan = {"primary_system": "economic"}
        mirror = {"gate_1_source_integrity": {"score": 80}}
        prompt = build_verdict_prompt("test", scan, mirror)
        assert "THE VERDICT" in prompt
        assert "economic" in prompt
        assert "80" in prompt

    def test_correction_prompt_contains_pass_number(self):
        verdict = {"total_score": 50}
        prompt = build_correction_prompt("test", verdict, 3)
        assert "SELF-CORRECTION PASS 3" in prompt
        assert "50" in prompt


# ---------------------------------------------------------------------------
# JSON Parsing
# ---------------------------------------------------------------------------

class TestJSONParsing:
    def setup_method(self):
        self.engine = ReasoningEngine(lambda p: "")

    def test_parse_clean_json(self):
        raw = '{"key": "value", "num": 42}'
        result = self.engine._parse_json(raw)
        assert result == {"key": "value", "num": 42}

    def test_parse_json_with_markdown_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        result = self.engine._parse_json(raw)
        assert result == {"key": "value"}

    def test_parse_json_with_surrounding_text(self):
        raw = 'Here is the result:\n{"key": "value"}\nEnd of response.'
        result = self.engine._parse_json(raw)
        assert result == {"key": "value"}

    def test_parse_json_with_code_fence_no_lang(self):
        raw = '```\n{"answer": true}\n```'
        result = self.engine._parse_json(raw)
        assert result == {"answer": True}

    def test_parse_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            self.engine._parse_json("not json at all")

    def test_parse_nested_json(self):
        raw = json.dumps({"outer": {"inner": [1, 2, 3]}})
        result = self.engine._parse_json(raw)
        assert result["outer"]["inner"] == [1, 2, 3]


# ---------------------------------------------------------------------------
# Engine Pipeline
# ---------------------------------------------------------------------------

class TestReasoningEnginePipeline:
    def test_scan(self, engine):
        result = engine.scan("Is interest-based lending just?")
        assert result["primary_system"] == "economic"
        assert len(result["friction_points"]) == 2

    def test_mirror(self):
        llm = make_mock_llm([MOCK_MIRROR_RESPONSE])
        engine = ReasoningEngine(llm)
        result = engine.mirror("test", {"primary_system": "economic"})
        assert result["gate_1_source_integrity"]["score"] == 85
        assert result["gate_4_origin_aware"]["result"] == "Survive"

    def test_verdict(self):
        llm = make_mock_llm([MOCK_VERDICT_RESPONSE])
        engine = ReasoningEngine(llm)
        result = engine.verdict("test", {}, {})
        assert result["total_score"] == 85
        assert "debt traps" in result["revised_reasoning"]

    def test_self_correct_sound(self):
        llm = make_mock_llm([MOCK_CORRECTION_SOUND])
        engine = ReasoningEngine(llm)
        result = engine.self_correct("test", {"total_score": 85}, 1)
        assert result["is_sound"] is True
        assert result["corrected_verdict"] is None

    def test_self_correct_with_fix(self):
        llm = make_mock_llm([MOCK_CORRECTION_WITH_FIX])
        engine = ReasoningEngine(llm)
        result = engine.self_correct("test", {"total_score": 85}, 1)
        assert result["is_sound"] is False
        assert result["corrected_verdict"]["total_score"] == 90

    def test_full_evaluate(self, engine):
        verdict = engine.evaluate("Is interest-based lending just?")
        assert isinstance(verdict, Verdict)
        assert verdict.primary_system == SystemType.ECONOMIC
        assert verdict.total_score == 85
        assert verdict.passes == 1
        assert len(verdict.gate_scores) == 3
        assert verdict.origin_gate == GateResult.SURVIVE

    def test_evaluate_with_correction(self):
        responses = [
            MOCK_SCAN_RESPONSE,
            MOCK_MIRROR_RESPONSE,
            MOCK_VERDICT_RESPONSE,
            MOCK_CORRECTION_WITH_FIX,
            MOCK_CORRECTION_SOUND,
        ]
        engine = ReasoningEngine(make_mock_llm(responses))
        verdict = engine.evaluate("test")
        assert verdict.total_score == 90  # corrected score
        assert verdict.passes == 2

    def test_evaluate_with_context(self, engine):
        verdict = engine.evaluate("test", context="prior verdict context")
        assert isinstance(verdict, Verdict)

    def test_max_correction_passes(self):
        # LLM always returns corrections, never sound
        never_sound = json.dumps({
            "contradictions_found": ["always wrong"],
            "is_sound": False,
            "corrected_verdict": {
                "consequences_short_term": [], "consequences_long_term": [],
                "actors_and_mechanisms": "", "revised_reasoning": "",
                "final_judgment": "", "total_score": 50,
            },
        })
        responses = [MOCK_SCAN_RESPONSE, MOCK_MIRROR_RESPONSE, MOCK_VERDICT_RESPONSE]
        responses += [never_sound] * 10  # more than MAX_CORRECTION_PASSES
        engine = ReasoningEngine(make_mock_llm(responses))
        engine.MAX_CORRECTION_PASSES = 3
        verdict = engine.evaluate("test")
        assert verdict.passes == 3  # stopped at max

    def test_build_verdict_object(self, engine):
        scan = json.loads(MOCK_SCAN_RESPONSE)
        mirror = json.loads(MOCK_MIRROR_RESPONSE)
        vdict = json.loads(MOCK_VERDICT_RESPONSE)
        verdict = engine._build_verdict_object("test", scan, mirror, vdict, 2)
        assert verdict.question == "test"
        assert verdict.passes == 2
        assert verdict.primary_system == SystemType.ECONOMIC

    def test_build_verdict_object_unknown_system(self, engine):
        scan = {"primary_system": "unknown_system", "friction_points": []}
        mirror = json.loads(MOCK_MIRROR_RESPONSE)
        vdict = json.loads(MOCK_VERDICT_RESPONSE)
        verdict = engine._build_verdict_object("test", scan, mirror, vdict, 1)
        assert verdict.primary_system == SystemType.MIXED

    def test_build_verdict_object_none_system(self, engine):
        scan = {"primary_system": None, "friction_points": []}
        mirror = json.loads(MOCK_MIRROR_RESPONSE)
        vdict = json.loads(MOCK_VERDICT_RESPONSE)
        verdict = engine._build_verdict_object("test", scan, mirror, vdict, 1)
        assert verdict.primary_system == SystemType.MIXED

    def test_build_gate_scores(self, engine):
        mirror = json.loads(MOCK_MIRROR_RESPONSE)
        scores = engine._build_gate_scores(mirror)
        assert len(scores) == 4
        assert scores[0].name == "Source-Integrity"
        assert scores[0].score == 85
        assert scores[3].name == "Origin-Aware"

    def test_build_gate_scores_missing_data(self, engine):
        scores = engine._build_gate_scores({})
        assert len(scores) == 4
        assert all(g.score == 0 for g in scores)
        assert all(g.result == GateResult.FAIL for g in scores)
