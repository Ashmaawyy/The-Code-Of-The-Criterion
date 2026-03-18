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
import logging
import sys
import time
from pathlib import Path

import pytest

# Ensure project root is on the path so bare module imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

logger = logging.getLogger("test_reasoning_engine")


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

class TestSystemType:
    def test_all_values(self):
        expected = {"economic", "social", "spiritual", "political",
                    "legal", "technological", "environmental", "mixed"}
        actual = {e.value for e in SystemType}
        logger.info("Checking SystemType enum values")
        logger.debug("Expected: %s", sorted(expected))
        logger.debug("Actual:   %s", sorted(actual))
        assert actual == expected
        logger.info("All %d SystemType values present", len(expected))

    def test_from_string(self):
        logger.info("Constructing SystemType from string values")
        econ = SystemType("economic")
        mixed = SystemType("mixed")
        logger.debug("'economic' → %s, 'mixed' → %s", econ, mixed)
        assert econ == SystemType.ECONOMIC
        assert mixed == SystemType.MIXED
        logger.info("String → SystemType conversion works")

    def test_invalid_raises(self):
        logger.info("Attempting to create SystemType from invalid string 'nonexistent'")
        with pytest.raises(ValueError):
            SystemType("nonexistent")
        logger.info("ValueError raised as expected")


class TestGateResult:
    def test_values(self):
        logger.info("Checking GateResult enum values")
        logger.debug("SURVIVE=%s, FAIL=%s", GateResult.SURVIVE.value, GateResult.FAIL.value)
        assert GateResult.SURVIVE.value == "Survive"
        assert GateResult.FAIL.value == "Fail"
        logger.info("GateResult values verified")


class TestGateScore:
    def test_to_dict(self):
        logger.info("Serializing GateScore (Source-Integrity, 85, Survive)")
        gs = GateScore("Source-Integrity", 85, GateResult.SURVIVE, "Solid data.")
        d = gs.to_dict()
        logger.debug("Serialized: %s", d)
        assert d == {
            "name": "Source-Integrity",
            "score": 85,
            "result": "Survive",
            "reasoning": "Solid data.",
        }
        logger.info("GateScore serialization correct")

    def test_fail_result(self):
        logger.info("Creating GateScore with FAIL result (score=30)")
        gs = GateScore("Test", 30, GateResult.FAIL, "Weak.")
        logger.debug("result=%s, dict.result=%s", gs.result, gs.to_dict()["result"])
        assert gs.result == GateResult.FAIL
        assert gs.to_dict()["result"] == "Fail"
        logger.info("FAIL GateScore serializes correctly")


class TestVerdict:
    def test_to_dict(self, sample_verdict):
        logger.info("Serializing sample_verdict to dict")
        d = sample_verdict.to_dict()
        logger.debug("question=%s, primary_system=%s, total_score=%s, gate_count=%d",
                      d["question"], d["primary_system"], d["total_score"], len(d["gate_scores"]))
        assert d["question"] == "Is interest-based lending just?"
        assert d["primary_system"] == "economic"
        assert d["total_score"] == 85
        assert d["origin_gate"] == "Survive"
        assert len(d["gate_scores"]) == 3
        assert d["gate_scores"][0]["name"] == "Source-Integrity"
        logger.info("Verdict.to_dict() output verified")

    def test_to_log(self, sample_verdict):
        logger.info("Generating human-readable log from sample_verdict")
        log = sample_verdict.to_log()
        logger.debug("Log output length: %d chars", len(log))
        assert "Question: Is interest-based lending just?" in log
        assert "Primary System Identified: economic" in log
        assert "Source-Integrity: 85/100 [Survive]" in log
        assert "Origin-Aware Gate: Survive" in log
        assert "Total Score: 85" in log
        logger.info("Verdict.to_log() contains all expected sections")

    def test_from_dict_roundtrip(self, sample_verdict):
        logger.info("Testing Verdict serialization → deserialization roundtrip")
        d = sample_verdict.to_dict()
        rebuilt = Verdict.from_dict(d)
        logger.debug("Original: question=%s, score=%d, passes=%d",
                      sample_verdict.question, sample_verdict.total_score, sample_verdict.passes)
        logger.debug("Rebuilt:  question=%s, score=%d, passes=%d",
                      rebuilt.question, rebuilt.total_score, rebuilt.passes)
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
        logger.info("Roundtrip serialization verified — all fields match")

    def test_from_dict_defaults(self):
        logger.info("Building Verdict from empty dict (should use all defaults)")
        v = Verdict.from_dict({})
        logger.debug("question='%s', system=%s, score=%d, gates=%d, origin=%s",
                      v.question, v.primary_system, v.total_score, len(v.gate_scores), v.origin_gate)
        assert v.question == ""
        assert v.primary_system == SystemType.MIXED
        assert v.total_score == 0
        assert v.gate_scores == []
        assert v.origin_gate == GateResult.FAIL
        logger.info("Empty dict defaults verified")

    def test_from_dict_invalid_system_type(self):
        logger.info("Building Verdict with invalid primary_system='invalid_system'")
        v = Verdict.from_dict({"primary_system": "invalid_system"})
        logger.debug("Resolved primary_system=%s (expected MIXED)", v.primary_system)
        assert v.primary_system == SystemType.MIXED
        logger.info("Invalid system type gracefully defaults to MIXED")

    def test_from_dict_string_score(self):
        logger.info("Building Verdict with string total_score='85'")
        v = Verdict.from_dict({"total_score": "85"})
        logger.debug("total_score=%d, type=%s", v.total_score, type(v.total_score).__name__)
        assert v.total_score == 85
        assert isinstance(v.total_score, int)
        logger.info("String score correctly cast to int")

    def test_timestamp_auto_set(self):
        logger.info("Testing auto-timestamp on Verdict creation")
        before = time.time()
        v = Verdict(
            question="test", primary_system=SystemType.MIXED,
            friction_points=[], gate_scores=[], origin_gate=GateResult.FAIL,
            consequences_short_term=[], consequences_long_term=[],
            revised_reasoning="", final_judgment="", total_score=0, passes=0,
        )
        after = time.time()
        logger.debug("before=%.3f, verdict.timestamp=%.3f, after=%.3f", before, v.timestamp, after)
        assert before <= v.timestamp <= after
        logger.info("Auto-timestamp within expected window")


# ---------------------------------------------------------------------------
# Prompt Builders
# ---------------------------------------------------------------------------

class TestPromptBuilders:
    def test_scan_prompt_contains_question(self):
        logger.info("Building scan prompt for 'Is democracy effective?'")
        prompt = build_scan_prompt("Is democracy effective?")
        logger.debug("Prompt length: %d chars", len(prompt))
        assert "Is democracy effective?" in prompt
        assert "THE SCAN" in prompt
        assert "TRANSCENDENCE NECESSITY PROOF" in prompt
        logger.info("Scan prompt contains question and required headers")

    def test_scan_prompt_with_context(self):
        logger.info("Building scan prompt with prior verdict context")
        prompt = build_scan_prompt("test question", context="prior verdict info")
        logger.debug("Context section present: %s", "Relevant prior verdicts" in prompt)
        assert "prior verdict info" in prompt
        assert "Relevant prior verdicts" in prompt
        logger.info("Scan prompt includes context section when context provided")

    def test_scan_prompt_without_context(self):
        logger.info("Building scan prompt with empty context")
        prompt = build_scan_prompt("test question", context="")
        logger.debug("Context section absent: %s", "Relevant prior verdicts" not in prompt)
        assert "Relevant prior verdicts" not in prompt
        logger.info("Scan prompt omits context section when context is empty")

    def test_mirror_prompt_contains_scan_result(self):
        scan = {"primary_system": "social", "friction_points": ["fp1"]}
        logger.info("Building mirror prompt with scan result: %s", scan)
        prompt = build_mirror_prompt("test", scan)
        logger.debug("Prompt length: %d chars", len(prompt))
        assert "THE MIRROR" in prompt
        assert '"primary_system": "social"' in prompt
        assert "TRI-AXIAL SURVIVAL GATES" in prompt
        logger.info("Mirror prompt contains scan data and required headers")

    def test_verdict_prompt_contains_both_results(self):
        scan = {"primary_system": "economic"}
        mirror = {"gate_1_source_integrity": {"score": 80}}
        logger.info("Building verdict prompt with scan=%s, mirror=%s", scan, mirror)
        prompt = build_verdict_prompt("test", scan, mirror)
        logger.debug("Prompt length: %d chars", len(prompt))
        assert "THE VERDICT" in prompt
        assert "economic" in prompt
        assert "80" in prompt
        logger.info("Verdict prompt contains both scan and mirror data")

    def test_correction_prompt_contains_pass_number(self):
        verdict = {"total_score": 50}
        logger.info("Building correction prompt for pass 3, verdict=%s", verdict)
        prompt = build_correction_prompt("test", verdict, 3)
        logger.debug("Prompt length: %d chars", len(prompt))
        assert "SELF-CORRECTION PASS 3" in prompt
        assert "50" in prompt
        logger.info("Correction prompt includes pass number and score")


# ---------------------------------------------------------------------------
# JSON Parsing
# ---------------------------------------------------------------------------

class TestJSONParsing:
    def setup_method(self):
        self.engine = ReasoningEngine(lambda p: "")
        logger.info("Created ReasoningEngine with no-op LLM for JSON parsing tests")

    def test_parse_clean_json(self):
        raw = '{"key": "value", "num": 42}'
        logger.info("Parsing clean JSON: %s", raw)
        result = self.engine._parse_json(raw)
        logger.debug("Parsed result: %s", result)
        assert result == {"key": "value", "num": 42}
        logger.info("Clean JSON parsed successfully")

    def test_parse_json_with_markdown_fences(self):
        raw = '```json\n{"key": "value"}\n```'
        logger.info("Parsing JSON wrapped in ```json fences")
        result = self.engine._parse_json(raw)
        logger.debug("Parsed result: %s", result)
        assert result == {"key": "value"}
        logger.info("Markdown-fenced JSON parsed successfully")

    def test_parse_json_with_surrounding_text(self):
        raw = 'Here is the result:\n{"key": "value"}\nEnd of response.'
        logger.info("Parsing JSON with surrounding text")
        result = self.engine._parse_json(raw)
        logger.debug("Parsed result: %s", result)
        assert result == {"key": "value"}
        logger.info("JSON extracted from surrounding text successfully")

    def test_parse_json_with_code_fence_no_lang(self):
        raw = '```\n{"answer": true}\n```'
        logger.info("Parsing JSON in code fence without language tag")
        result = self.engine._parse_json(raw)
        logger.debug("Parsed result: %s", result)
        assert result == {"answer": True}
        logger.info("Language-less code fence JSON parsed successfully")

    def test_parse_invalid_json_raises(self):
        logger.info("Attempting to parse invalid JSON: 'not json at all'")
        with pytest.raises(json.JSONDecodeError):
            self.engine._parse_json("not json at all")
        logger.info("JSONDecodeError raised as expected for invalid input")

    def test_parse_nested_json(self):
        raw = json.dumps({"outer": {"inner": [1, 2, 3]}})
        logger.info("Parsing nested JSON: %s", raw)
        result = self.engine._parse_json(raw)
        logger.debug("Parsed result: %s", result)
        assert result["outer"]["inner"] == [1, 2, 3]
        logger.info("Nested JSON parsed correctly")


# ---------------------------------------------------------------------------
# Engine Pipeline
# ---------------------------------------------------------------------------

class TestReasoningEnginePipeline:
    def test_scan(self, engine):
        logger.info("Running engine.scan('Is interest-based lending just?')")
        result = engine.scan("Is interest-based lending just?")
        logger.debug("Scan result: primary_system=%s, friction_points=%s",
                      result["primary_system"], result["friction_points"])
        assert result["primary_system"] == "economic"
        assert len(result["friction_points"]) == 2
        logger.info("Scan returned expected system and %d friction points", len(result["friction_points"]))

    def test_mirror(self):
        logger.info("Running engine.mirror with mock mirror response")
        llm = make_mock_llm([MOCK_MIRROR_RESPONSE])
        engine = ReasoningEngine(llm)
        result = engine.mirror("test", {"primary_system": "economic"})
        logger.debug("Mirror result — gate_1 score=%d, gate_4 result=%s",
                      result["gate_1_source_integrity"]["score"],
                      result["gate_4_origin_aware"]["result"])
        assert result["gate_1_source_integrity"]["score"] == 85
        assert result["gate_4_origin_aware"]["result"] == "Survive"
        logger.info("Mirror returned correct gate scores")

    def test_verdict(self):
        logger.info("Running engine.verdict with mock verdict response")
        llm = make_mock_llm([MOCK_VERDICT_RESPONSE])
        engine = ReasoningEngine(llm)
        result = engine.verdict("test", {}, {})
        logger.debug("Verdict result — total_score=%d, reasoning='%s'",
                      result["total_score"], result["revised_reasoning"][:50])
        assert result["total_score"] == 85
        assert "debt traps" in result["revised_reasoning"]
        logger.info("Verdict returned expected score and reasoning")

    def test_self_correct_sound(self):
        logger.info("Running engine.self_correct — verdict IS sound")
        llm = make_mock_llm([MOCK_CORRECTION_SOUND])
        engine = ReasoningEngine(llm)
        result = engine.self_correct("test", {"total_score": 85}, 1)
        logger.debug("Correction result — is_sound=%s, corrected_verdict=%s",
                      result["is_sound"], result["corrected_verdict"])
        assert result["is_sound"] is True
        assert result["corrected_verdict"] is None
        logger.info("Sound verdict correctly identified — no correction needed")

    def test_self_correct_with_fix(self):
        logger.info("Running engine.self_correct — verdict needs correction")
        llm = make_mock_llm([MOCK_CORRECTION_WITH_FIX])
        engine = ReasoningEngine(llm)
        result = engine.self_correct("test", {"total_score": 85}, 1)
        logger.debug("Correction result — is_sound=%s, new_score=%d, contradictions=%s",
                      result["is_sound"], result["corrected_verdict"]["total_score"],
                      result["contradictions_found"])
        assert result["is_sound"] is False
        assert result["corrected_verdict"]["total_score"] == 90
        logger.info("Correction applied: score changed from 85 → 90")

    def test_full_evaluate(self, engine):
        logger.info("Running full engine.evaluate('Is interest-based lending just?')")
        verdict = engine.evaluate("Is interest-based lending just?")
        logger.debug("Verdict: system=%s, score=%d, passes=%d, gates=%d, origin=%s",
                      verdict.primary_system.value, verdict.total_score, verdict.passes,
                      len(verdict.gate_scores), verdict.origin_gate.value)
        assert isinstance(verdict, Verdict)
        assert verdict.primary_system == SystemType.ECONOMIC
        assert verdict.total_score == 85
        assert verdict.passes == 1
        assert len(verdict.gate_scores) == 3
        assert verdict.origin_gate == GateResult.SURVIVE
        logger.info("Full evaluation pipeline completed successfully")

    def test_evaluate_with_correction(self):
        logger.info("Running full evaluate with one correction pass")
        responses = [
            MOCK_SCAN_RESPONSE,
            MOCK_MIRROR_RESPONSE,
            MOCK_VERDICT_RESPONSE,
            MOCK_CORRECTION_WITH_FIX,
            MOCK_CORRECTION_SOUND,
        ]
        engine = ReasoningEngine(make_mock_llm(responses))
        verdict = engine.evaluate("test")
        logger.debug("Verdict after correction: score=%d, passes=%d", verdict.total_score, verdict.passes)
        assert verdict.total_score == 90  # corrected score
        assert verdict.passes == 2
        logger.info("Evaluation with correction: score 85→90 over %d passes", verdict.passes)

    def test_evaluate_with_context(self, engine):
        logger.info("Running evaluate with prior verdict context")
        verdict = engine.evaluate("test", context="prior verdict context")
        logger.debug("Verdict type: %s", type(verdict).__name__)
        assert isinstance(verdict, Verdict)
        logger.info("Evaluate with context completed successfully")

    def test_max_correction_passes(self):
        logger.info("Testing MAX_CORRECTION_PASSES enforcement (limit=3)")
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
        logger.debug("Verdict passes=%d (should be capped at 3)", verdict.passes)
        assert verdict.passes == 3  # stopped at max
        logger.info("Correction loop correctly capped at %d passes", verdict.passes)

    def test_build_verdict_object(self, engine):
        logger.info("Testing _build_verdict_object from raw dicts")
        scan = json.loads(MOCK_SCAN_RESPONSE)
        mirror = json.loads(MOCK_MIRROR_RESPONSE)
        vdict = json.loads(MOCK_VERDICT_RESPONSE)
        verdict = engine._build_verdict_object("test", scan, mirror, vdict, 2)
        logger.debug("Built verdict: question=%s, system=%s, passes=%d",
                      verdict.question, verdict.primary_system.value, verdict.passes)
        assert verdict.question == "test"
        assert verdict.passes == 2
        assert verdict.primary_system == SystemType.ECONOMIC
        logger.info("Verdict object built correctly from raw dicts")

    def test_build_verdict_object_unknown_system(self, engine):
        logger.info("Testing _build_verdict_object with unknown system type")
        scan = {"primary_system": "unknown_system", "friction_points": []}
        mirror = json.loads(MOCK_MIRROR_RESPONSE)
        vdict = json.loads(MOCK_VERDICT_RESPONSE)
        verdict = engine._build_verdict_object("test", scan, mirror, vdict, 1)
        logger.debug("Resolved system: %s (expected MIXED)", verdict.primary_system.value)
        assert verdict.primary_system == SystemType.MIXED
        logger.info("Unknown system type gracefully defaults to MIXED")

    def test_build_verdict_object_none_system(self, engine):
        logger.info("Testing _build_verdict_object with None system type")
        scan = {"primary_system": None, "friction_points": []}
        mirror = json.loads(MOCK_MIRROR_RESPONSE)
        vdict = json.loads(MOCK_VERDICT_RESPONSE)
        verdict = engine._build_verdict_object("test", scan, mirror, vdict, 1)
        logger.debug("Resolved system: %s (expected MIXED)", verdict.primary_system.value)
        assert verdict.primary_system == SystemType.MIXED
        logger.info("None system type gracefully defaults to MIXED")

    def test_build_gate_scores(self, engine):
        logger.info("Testing _build_gate_scores from mirror response")
        mirror = json.loads(MOCK_MIRROR_RESPONSE)
        scores = engine._build_gate_scores(mirror)
        logger.debug("Built %d gate scores:", len(scores))
        for gs in scores:
            logger.debug("  %s: %d/100 [%s]", gs.name, gs.score, gs.result.value)
        assert len(scores) == 4
        assert scores[0].name == "Source-Integrity"
        assert scores[0].score == 85
        assert scores[3].name == "Origin-Aware"
        logger.info("Gate scores built correctly from mirror data")

    def test_build_gate_scores_missing_data(self, engine):
        logger.info("Testing _build_gate_scores from empty dict (all defaults)")
        scores = engine._build_gate_scores({})
        logger.debug("Built %d gate scores (all should be 0/FAIL):", len(scores))
        for gs in scores:
            logger.debug("  %s: %d/100 [%s]", gs.name, gs.score, gs.result.value)
        assert len(scores) == 4
        assert all(g.score == 0 for g in scores)
        assert all(g.result == GateResult.FAIL for g in scores)
        logger.info("Missing mirror data produces 4 zero-score FAIL gates")
