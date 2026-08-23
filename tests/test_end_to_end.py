"""End-to-end integration tests for the full Al-Furqan pipeline.

Tests the complete flow: question → orchestrator → EvaluationResult
using mock LLM (no real API calls).
"""

import asyncio
import json
from unittest.mock import MagicMock  # pylint: disable=wrong-import-order

from al_furqan.api.orchestrator import EvaluationResult, Orchestrator
from al_furqan.engine.models import (  # pylint: disable=unused-import
    GateResult,
    Verdict,
)
from al_furqan.engine.pipeline import EvaluationPipeline
from al_furqan.engine.symbolic.verifier import SymbolicVerifier, VerificationResult

# ── Mock LLM ──

# Deterministic LLM responses for known questions
_SCAN_RESPONSE = json.dumps(
    {
        "primary_system": "economic",
        "friction_points": ["single source of truth limits diversity", "monopoly risk"],
        "effects": ["cultural homogenization", "reduced pluralism"],
    }
)

_MIRROR_RESPONSE = json.dumps(
    {
        "gate_1_source_integrity": {
            "score": 20,
            "result": "Fail",
            "reasoning": "Accepting only one source of truth is reductive",
        },
        "gate_2_structural_consistency": {
            "score": 15,
            "result": "Fail",
            "reasoning": "Structurally inconsistent with Islamic scholarship tradition",
        },
        "gate_3_mediation_zeroing": {
            "score": 10,
            "result": "Fail",
            "reasoning": "Zeroing out mediation pathways",
        },
        "gate_4_origin_aware": {
            "score": 20,
            "result": "Fail",
            "reasoning": "Does not align with origin principles",
        },
    }
)

_VERDICT_RESPONSE = json.dumps(
    {
        "consequences_short_term": ["suppression of legitimate scholarly debate"],
        "consequences_long_term": ["intellectual stagnation"],
        "revised_reasoning": "Single source dogma contradicts the rich tradition of ijtihad",
        "final_judgment": "FAIL — restricting truth to one source contradicts Islamic epistemology",
        "total_score": 16,
    }
)

_CORRECTION_SOUND = json.dumps(
    {
        "is_sound": True,
        "contradictions_found": [],
        "corrected_verdict": None,
    }
)

# For dual perspective question
_INTENT_DUAL = json.dumps(
    {
        "intent_type": "system_evaluation",
        "target_system": "single source acceptance framework",
        "embedded_assumptions": [
            "accepting one source might offend",
            "offense is a valid reason to reject truth",
        ],
        "neutralized_question": "Should a framework accept only one source of truth?",
    }
)

_INTENT_SIMPLE = json.dumps(
    {
        "intent_type": "claim_judgment",
        "target_system": "single source of truth framework",
        "embedded_assumptions": [],
        "neutralized_question": "Should you accept only one source of truth?",
    }
)


class MockLLMSequence:  # pylint: disable=too-few-public-methods
    """Mock LLM that returns predetermined responses in sequence."""

    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self._index = 0

    def __call__(self, prompt: str) -> str:
        if self._index >= len(self._responses):
            # Loop back for correction passes
            return _CORRECTION_SOUND
        response = self._responses[self._index]
        self._index += 1
        return response


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Tests ──


class TestFullPipelineE2E:
    """End-to-end: question → EvaluationPipeline → Orchestrator → EvaluationResult."""

    def test_single_source_of_truth_all_fail(self):
        """
        Question 1: "Should you accept only one source of truth..."
        Expected: ALL gates FAIL.
        """
        mock_llm = MockLLMSequence(
            [
                _SCAN_RESPONSE,
                _MIRROR_RESPONSE,
                _VERDICT_RESPONSE,
                _CORRECTION_SOUND,
            ]
        )

        pipeline = EvaluationPipeline(llm_call=mock_llm)
        response_llm = MagicMock(
            return_value="Single source of truth is rejected by the evaluation."
        )  # pylint: disable=line-too-long

        orch = Orchestrator(engine_pipeline=pipeline, llm_fn=response_llm)
        result = _run(orch.evaluate("Should you accept only one source of truth?"))

        assert isinstance(result, EvaluationResult)
        assert result.verdict is not None
        assert result.verdict.total_score <= 30  # Low score — all fail
        # All 3 tri-axial gates should fail
        for gs in result.verdict.gate_scores:
            assert gs.result == GateResult.FAIL
        assert (
            result.response_text
            == "Single source of truth is rejected by the evaluation."
        )
        assert result.evaluation_id.startswith("eval_")

    def test_result_has_both_response_and_verdict(self):
        """EvaluationResult must have both response_text (user) and verdict (internal)."""
        mock_llm = MockLLMSequence(
            [
                _SCAN_RESPONSE,
                _MIRROR_RESPONSE,
                _VERDICT_RESPONSE,
                _CORRECTION_SOUND,
            ]
        )
        pipeline = EvaluationPipeline(llm_call=mock_llm)
        orch = Orchestrator(engine_pipeline=pipeline)

        result = _run(orch.evaluate("test question"))
        # response_text is user-facing
        assert isinstance(result.response_text, str)
        assert len(result.response_text) > 0
        # verdict is internal
        assert isinstance(result.verdict, Verdict)
        assert hasattr(result.verdict, "gate_scores")
        assert hasattr(result.verdict, "total_score")

    def test_pipeline_with_z3_verification(self):
        """Z3 verification integrates with the full pipeline."""
        mock_llm = MockLLMSequence(
            [
                _SCAN_RESPONSE,
                _MIRROR_RESPONSE,
                _VERDICT_RESPONSE,
                _CORRECTION_SOUND,
            ]
        )
        pipeline = EvaluationPipeline(llm_call=mock_llm)
        verifier = SymbolicVerifier(timeout_ms=5000)

        orch = Orchestrator(engine_pipeline=pipeline, symbolic_verifier=verifier)
        result = _run(orch.evaluate("test", use_z3=True))
        assert result.z3_result is not None
        assert isinstance(result.z3_result, VerificationResult)

    def test_pipeline_without_kb(self):
        """Pipeline works fine without KB."""
        mock_llm = MockLLMSequence(
            [
                _SCAN_RESPONSE,
                _MIRROR_RESPONSE,
                _VERDICT_RESPONSE,
                _CORRECTION_SOUND,
            ]
        )
        pipeline = EvaluationPipeline(llm_call=mock_llm)
        orch = Orchestrator(engine_pipeline=pipeline)
        result = _run(orch.evaluate("test", use_kb=True))
        # No KB configured, so sources should be empty
        assert result.sources == []

    def test_evaluation_result_to_log_dict_complete(self):
        """to_log_dict should contain all evaluation data."""
        mock_llm = MockLLMSequence(
            [
                _SCAN_RESPONSE,
                _MIRROR_RESPONSE,
                _VERDICT_RESPONSE,
                _CORRECTION_SOUND,
            ]
        )
        pipeline = EvaluationPipeline(llm_call=mock_llm)
        orch = Orchestrator(engine_pipeline=pipeline)
        result = _run(orch.evaluate("test"))

        log = result.to_log_dict()
        assert "evaluation_id" in log
        assert "verdict" in log
        assert "response_text" in log
        assert "processing_time_ms" in log
        assert log["processing_time_ms"] >= 0

    def test_processing_time_measured(self):
        """Processing time should be positive and realistic."""
        mock_llm = MockLLMSequence(
            [
                _SCAN_RESPONSE,
                _MIRROR_RESPONSE,
                _VERDICT_RESPONSE,
                _CORRECTION_SOUND,
            ]
        )
        pipeline = EvaluationPipeline(llm_call=mock_llm)
        orch = Orchestrator(engine_pipeline=pipeline)
        result = _run(orch.evaluate("test"))
        assert result.processing_time_ms > 0
        # Should be less than 10 seconds for mock
        assert result.processing_time_ms < 10000

    def test_each_evaluation_gets_unique_id(self):
        """Every evaluation should get a unique ID."""
        mock_llm = MockLLMSequence(
            [_SCAN_RESPONSE, _MIRROR_RESPONSE, _VERDICT_RESPONSE, _CORRECTION_SOUND] * 3
        )
        pipeline = EvaluationPipeline(llm_call=mock_llm)
        orch = Orchestrator(engine_pipeline=pipeline)

        ids = set()
        for _ in range(3):
            result = _run(orch.evaluate("test"))
            ids.add(result.evaluation_id)
        assert len(ids) == 3

    def test_verdict_contains_gate_details(self):
        """Internal verdict should have full gate scoring details."""
        mock_llm = MockLLMSequence(
            [
                _SCAN_RESPONSE,
                _MIRROR_RESPONSE,
                _VERDICT_RESPONSE,
                _CORRECTION_SOUND,
            ]
        )
        pipeline = EvaluationPipeline(llm_call=mock_llm)
        orch = Orchestrator(engine_pipeline=pipeline)
        result = _run(orch.evaluate("test"))

        assert len(result.verdict.gate_scores) == 3
        for gs in result.verdict.gate_scores:
            assert gs.name in [
                "Source-Integrity",
                "Structural-Consistency",
                "Mediation-Zeroing",
            ]
            assert 0 <= gs.score <= 100
            assert gs.result in [GateResult.SURVIVE, GateResult.FAIL]
            assert len(gs.reasoning) > 0
