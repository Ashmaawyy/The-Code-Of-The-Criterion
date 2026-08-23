"""Tests for the Orchestrator — the central integration layer."""

import asyncio
from unittest.mock import MagicMock  # pylint: disable=wrong-import-order

# pylint: disable=wrong-import-order
from al_furqan.api.orchestrator import EvaluationResult, Orchestrator, generate_eval_id
from al_furqan.engine.models import (  # pylint: disable=unused-import
    GateResult,
    GateScore,
    SystemType,
    Verdict,
)
from al_furqan.engine.symbolic.verifier import VerificationResult

# ── Helpers ──


def _make_verdict(**overrides) -> Verdict:
    defaults = dict(  # pylint: disable=use-dict-literal
        question="Is interest-based banking permissible?",
        primary_system=SystemType.ECONOMIC,
        friction_points=["riba", "exploitation"],
        gate_scores=[
            GateScore(
                name="Source-Integrity",
                score=30,
                result=GateResult.FAIL,
                reasoning="No Quranic basis",
            ),  # pylint: disable=line-too-long
            GateScore(
                name="Structural-Consistency",
                score=25,
                result=GateResult.FAIL,
                reasoning="Contradicts",
            ),  # pylint: disable=line-too-long
            GateScore(
                name="Mediation-Zeroing",
                score=20,
                result=GateResult.FAIL,
                reasoning="Harmful",
            ),  # pylint: disable=line-too-long
        ],
        origin_gate=GateResult.FAIL,
        consequences_short_term=["debt accumulation"],
        consequences_long_term=["systemic inequality"],
        revised_reasoning="Interest-based banking contradicts Islamic principles",
        final_judgment="FAIL — riba is explicitly prohibited",
        total_score=25,
        passes=1,
    )
    defaults.update(overrides)
    return Verdict(**defaults)


def _make_mock_engine(verdict=None):
    engine = MagicMock()
    engine.evaluate.return_value = verdict or _make_verdict()
    return engine


def _make_mock_verifier(consistent=True):
    verifier = MagicMock()
    verifier.verify_verdict.return_value = VerificationResult(
        consistent=consistent,
        proof="Consistent with axioms" if consistent else "Contradicts axioms",
        verification_time_ms=5.0,
    )
    return verifier


def _run(coro):
    """Helper to run async in sync tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ── Tests ──


class TestEvalId:
    """TestEvalId class."""

    def test_generate_eval_id_unique(self):
        """Test generate_eval_id_unique."""
        ids = {generate_eval_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generate_eval_id_prefix(self):
        """Test generate_eval_id_prefix."""
        assert generate_eval_id().startswith("eval_")


class TestOrchestratorBasic:
    """TestOrchestratorBasic class."""

    def test_init_minimal(self):
        """Test init_minimal."""
        engine = _make_mock_engine()
        orch = Orchestrator(engine_pipeline=engine)
        assert orch.engine is engine
        assert orch.kb is None
        assert orch.verifier is None

    def test_init_all_components(self):
        """Test init_all_components."""
        engine = _make_mock_engine()
        kb = MagicMock()
        verifier = _make_mock_verifier()
        store = MagicMock()
        feedback = MagicMock()
        orch = Orchestrator(
            engine_pipeline=engine,
            kb_retriever=kb,
            symbolic_verifier=verifier,
            verdict_store=store,
            feedback_store=feedback,
            llm_fn=lambda p: "response",
        )
        assert orch.kb is kb
        assert orch.verifier is verifier
        assert orch.store is store
        assert orch.feedback is feedback


class TestEvaluate:
    """TestEvaluate class."""

    def test_evaluate_basic_no_kb_no_z3(self):
        """Test evaluate_basic_no_kb_no_z3."""
        engine = _make_mock_engine()
        orch = Orchestrator(engine_pipeline=engine)
        result = _run(orch.evaluate("Is riba allowed?", use_kb=False, use_z3=False))

        assert isinstance(result, EvaluationResult)
        assert result.verdict is not None
        assert result.evaluation_id.startswith("eval_")
        assert result.processing_time_ms >= 0
        assert result.sources == []
        assert result.z3_result is None

    def test_evaluate_calls_engine(self):
        """Test evaluate_calls_engine."""
        engine = _make_mock_engine()
        orch = Orchestrator(engine_pipeline=engine)
        _run(orch.evaluate("test question"))
        engine.evaluate.assert_called_once()
        call_args = engine.evaluate.call_args
        assert call_args[0][0] == "test question"

    def test_evaluate_with_z3(self):
        """Test evaluate_with_z3."""
        engine = _make_mock_engine()
        verifier = _make_mock_verifier(consistent=True)
        orch = Orchestrator(engine_pipeline=engine, symbolic_verifier=verifier)
        result = _run(orch.evaluate("test", use_z3=True))

        assert result.z3_result is not None
        assert result.z3_result.consistent is True
        verifier.verify_verdict.assert_called_once()

    def test_evaluate_with_kb(self):
        """Test evaluate_with_kb."""
        engine = _make_mock_engine()
        kb = MagicMock()
        kb_result = MagicMock()
        kb_result.formatted_context = "Quran 2:275 - Allah has permitted trade..."
        kb_result.sources = ["quran:2:275"]
        kb.retrieve.return_value = kb_result

        orch = Orchestrator(engine_pipeline=engine, kb_retriever=kb)
        result = _run(orch.evaluate("Is trade allowed?", use_kb=True))

        kb.retrieve.assert_called_once_with("Is trade allowed?")
        assert result.sources == ["quran:2:275"]
        # Engine should have been called with context
        call_args = engine.evaluate.call_args
        assert "Quran 2:275" in call_args[1].get(
            "context", call_args[0][1] if len(call_args[0]) > 1 else ""
        )  # pylint: disable=line-too-long

    def test_evaluate_stores_verdict(self):
        """Test evaluate_stores_verdict."""
        engine = _make_mock_engine()
        store = MagicMock()
        orch = Orchestrator(engine_pipeline=engine, verdict_store=store)
        _run(orch.evaluate("test"))
        store.store.assert_called_once()

    def test_evaluate_without_store(self):
        """Test evaluate_without_store."""
        engine = _make_mock_engine()
        orch = Orchestrator(engine_pipeline=engine)
        # Should not raise even without store
        result = _run(orch.evaluate("test"))
        assert result.verdict is not None


class TestResponseGeneration:
    """TestResponseGeneration class."""

    def test_response_with_llm_fn(self):
        """Test response_with_llm_fn."""
        engine = _make_mock_engine()
        llm_fn = MagicMock(return_value="Riba is clearly prohibited in Islam.")
        orch = Orchestrator(engine_pipeline=engine, llm_fn=llm_fn)
        result = _run(orch.evaluate("Is riba allowed?"))

        assert result.response_text == "Riba is clearly prohibited in Islam."
        llm_fn.assert_called_once()

    def test_response_fallback_to_judgment(self):
        """Test response_fallback_to_judgment."""
        verdict = _make_verdict(final_judgment="FAIL — prohibited")
        engine = _make_mock_engine(verdict=verdict)
        orch = Orchestrator(engine_pipeline=engine)
        result = _run(orch.evaluate("test"))

        assert result.response_text == "FAIL — prohibited"

    def test_response_fallback_no_judgment(self):
        """Test response_fallback_no_judgment."""
        verdict = _make_verdict(final_judgment="", total_score=42)
        engine = _make_mock_engine(verdict=verdict)
        orch = Orchestrator(engine_pipeline=engine)
        result = _run(orch.evaluate("test"))

        assert "42" in result.response_text

    def test_response_llm_failure_fallback(self):
        """Test response_llm_failure_fallback."""
        engine = _make_mock_engine()
        llm_fn = MagicMock(side_effect=RuntimeError("API down"))
        orch = Orchestrator(engine_pipeline=engine, llm_fn=llm_fn)
        result = _run(orch.evaluate("test"))

        # Should fallback to judgment
        assert result.response_text is not None
        assert len(result.response_text) > 0


class TestEvaluateGrounded:  # pylint: disable=too-few-public-methods
    """TestEvaluateGrounded class."""

    def test_evaluate_grounded_uses_kb_and_z3(self):
        """Test evaluate_grounded_uses_kb_and_z3."""
        engine = _make_mock_engine()
        kb = MagicMock()
        kb_result = MagicMock()
        kb_result.formatted_context = "context"
        kb_result.sources = ["src1"]
        kb.retrieve.return_value = kb_result
        verifier = _make_mock_verifier()

        orch = Orchestrator(
            engine_pipeline=engine, kb_retriever=kb, symbolic_verifier=verifier
        )
        result = _run(orch.evaluate_grounded("test"))

        kb.retrieve.assert_called_once()
        verifier.verify_verdict.assert_called_once()
        assert result.z3_result is not None
        assert result.sources == ["src1"]


class TestEvaluationResult:
    """TestEvaluationResult class."""

    def test_to_log_dict(self):
        """Test to_log_dict."""
        verdict = _make_verdict()
        result = EvaluationResult(
            response_text="Test response",
            verdict=verdict,
            evaluation_id="eval_123",
            processing_time_ms=150.0,
        )
        log = result.to_log_dict()
        assert log["evaluation_id"] == "eval_123"
        assert log["response_text"] == "Test response"
        assert "verdict" in log
        assert log["processing_time_ms"] == 150.0

    def test_to_log_dict_with_z3(self):
        """Test to_log_dict_with_z3."""
        verdict = _make_verdict()
        z3 = VerificationResult(consistent=True, proof="OK", verification_time_ms=5.0)
        result = EvaluationResult(response_text="Test", verdict=verdict, z3_result=z3)
        log = result.to_log_dict()
        assert log["z3_result"]["consistent"] is True

    def test_to_user_response(self):
        """Test to_user_response."""
        verdict = _make_verdict()
        result = EvaluationResult(response_text="Human readable", verdict=verdict)
        assert result.to_user_response() == "Human readable"

    def test_evaluation_result_defaults(self):
        """Test evaluation_result_defaults."""
        verdict = _make_verdict()
        result = EvaluationResult(response_text="test", verdict=verdict)
        assert result.dual_verdict is None
        assert not result.sources
        assert result.z3_result is None
        assert result.evaluation_id == ""
        assert result.model_used == ""


class TestErrorHandling:
    """TestErrorHandling class."""

    def test_kb_failure_doesnt_crash(self):
        """Test kb_failure_doesnt_crash."""
        engine = _make_mock_engine()
        kb = MagicMock()
        kb.retrieve.side_effect = RuntimeError("KB offline")
        orch = Orchestrator(engine_pipeline=engine, kb_retriever=kb)
        # Should not raise
        result = _run(orch.evaluate("test", use_kb=True))
        assert result.verdict is not None
        assert result.sources == []

    def test_z3_failure_doesnt_crash(self):
        """Test z3_failure_doesnt_crash."""
        engine = _make_mock_engine()
        verifier = MagicMock()
        verifier.verify_verdict.side_effect = RuntimeError("Z3 error")
        orch = Orchestrator(engine_pipeline=engine, symbolic_verifier=verifier)
        result = _run(orch.evaluate("test", use_z3=True))
        assert result.z3_result is None

    def test_store_failure_doesnt_crash(self):
        """Test store_failure_doesnt_crash."""
        engine = _make_mock_engine()
        store = MagicMock()
        store.store.side_effect = RuntimeError("disk full")
        orch = Orchestrator(engine_pipeline=engine, verdict_store=store)
        result = _run(orch.evaluate("test"))
        assert result.verdict is not None
