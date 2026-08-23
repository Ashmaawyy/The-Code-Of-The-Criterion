"""
Integration tests for the Engine refactor validation.

Tests: Module imports, backward compatibility, axiom hash consistency, pipeline structure.
"""

import json
import logging

logger = logging.getLogger(__name__)


class TestEngineModules:
    """Verify all engine modules export correctly."""

    def test_engine_modules_consistent(self):
        """Verify all engine modules import and export correctly."""
        from al_furqan.engine.axioms import (  # pylint: disable=import-outside-toplevel
            AXIOM_HASH,
            AXIOM_VERSION,
            AXIOMS,
            GATE_DEFINITIONS,
        )
        from al_furqan.engine.models import (  # pylint: disable=import-outside-toplevel
            GateResult,
            SystemType,
        )
        from al_furqan.engine.pipeline import (
            EvaluationPipeline,  # pylint: disable=import-outside-toplevel
        )
        from al_furqan.engine.prompts import (
            build_scan_prompt,  # pylint: disable=import-outside-toplevel
        )

        # Assert all imports are usable
        assert AXIOMS is not None and len(AXIOMS) > 0
        assert GATE_DEFINITIONS is not None and len(GATE_DEFINITIONS) > 0
        assert AXIOM_HASH is not None and len(AXIOM_HASH) > 0
        assert AXIOM_VERSION is not None
        assert callable(build_scan_prompt)
        assert callable(EvaluationPipeline)

        # Enums should have expected members
        assert SystemType.ECONOMIC.value == "economic"
        assert GateResult.SURVIVE.value == "Survive"
        assert GateResult.FAIL.value == "Fail"

        logger.info("All engine module exports verified")

    def test_engine_init_exports(self):
        """Verify engine __init__.py re-exports key symbols."""
        from al_furqan.engine import (  # pylint: disable=import-outside-toplevel
            axioms,
            models,
            pipeline,
            prompts,
        )

        assert hasattr(models, "Verdict")
        assert hasattr(axioms, "AXIOM_HASH")
        assert hasattr(prompts, "build_scan_prompt")
        assert hasattr(pipeline, "EvaluationPipeline")


class TestBackwardCompatibility:
    """Verify old import paths still work via the wrapper module."""

    def test_backward_compatibility_reasoning_engine(self):
        """Verify old import paths still work."""
        from al_furqan.core.reasoning_engine import (  # pylint: disable=import-outside-toplevel
            AXIOM_HASH,  # pylint: disable=import-outside-toplevel
            GateScore,
            ReasoningEngine,  # pylint: disable=import-outside-toplevel
            Verdict,
        )

        assert ReasoningEngine is not None
        assert Verdict is not None
        assert GateScore is not None
        assert AXIOM_HASH is not None
        logger.info("Backward compatibility verified: all old imports work")

    def test_old_and_new_imports_are_same_objects(self):
        """Verify old and new imports resolve to the same objects."""
        from al_furqan.core.reasoning_engine import (
            Verdict as OldVerdict,  # pylint: disable=import-outside-toplevel
        )
        from al_furqan.engine.models import (
            Verdict as NewVerdict,  # pylint: disable=import-outside-toplevel
        )

        assert OldVerdict is NewVerdict, "Old and new Verdict should be the same class"

        from al_furqan.core.reasoning_engine import (
            AXIOM_HASH as old_hash,  # pylint: disable=import-outside-toplevel
        )
        from al_furqan.engine.axioms import (
            AXIOM_HASH as new_hash,  # pylint: disable=import-outside-toplevel
        )

        assert old_hash == new_hash, (
            "Axiom hash should be identical via old and new paths"
        )


class TestAxiomHashConsistency:
    """Verify axiom hash is deterministic."""

    def test_axiom_hash_consistency(self):
        """Import AXIOM_HASH multiple times, verify it's the same."""
        from al_furqan.engine.axioms import (
            AXIOM_HASH as hash1,  # pylint: disable=import-outside-toplevel
        )

        # Force a fresh computation by importing the function
        from al_furqan.engine.axioms import (
            _compute_axiom_hash,  # pylint: disable=import-outside-toplevel
        )

        hash2 = _compute_axiom_hash()

        assert hash1 == hash2, f"Hash mismatch: {hash1} != {hash2}"
        assert len(hash1) == 64, f"Expected SHA-256 hex (64 chars), got {len(hash1)}"
        logger.info("Axiom hash is deterministic: %s", hash1[:16] + "...")

    def test_axiom_hash_is_sha256(self):
        """Verify axiom hash looks like a valid SHA-256 hex digest."""
        from al_furqan.engine.axioms import (
            AXIOM_HASH,  # pylint: disable=import-outside-toplevel
        )

        assert all(c in "0123456789abcdef" for c in AXIOM_HASH), (
            "Hash should be lowercase hex"
        )
        assert len(AXIOM_HASH) == 64


class TestPipelineWithoutContext:
    """Test EvaluationPipeline works without KB context (mocked LLM)."""

    def _make_mock_llm(self):
        """Create a mock LLM that returns valid JSON for each pipeline phase."""
        call_count = [0]

        def mock_llm(prompt: str) -> str:
            call_count[0] += 1
            prompt_lower = prompt.lower()
            # Detect which phase — check mirror FIRST (it also contains "scan" text)
            if "the mirror" in prompt_lower:  # pylint: disable=no-else-return
                return json.dumps(
                    {
                        "gate_scores": [
                            {
                                "name": "Source-Integrity",
                                "score": 80,
                                "result": "Survive",
                                "reasoning": "Clear evidence",
                            },  # pylint: disable=line-too-long
                            {
                                "name": "Maqasid-Alignment",
                                "score": 75,
                                "result": "Survive",
                                "reasoning": "Protects wealth",
                            },  # pylint: disable=line-too-long
                            {
                                "name": "Contextual-Sensitivity",
                                "score": 70,
                                "result": "Survive",
                                "reasoning": "Context aware",
                            },  # pylint: disable=line-too-long
                        ],
                        "origin_gate": "Survive",
                    }
                )
            elif "the scan" in prompt_lower:
                return json.dumps(
                    {
                        "primary_system": "economic",
                        "friction_points": ["interest", "debt"],
                        "consequences_short_term": ["quick profit"],
                        "consequences_long_term": ["economic instability"],
                    }
                )
            elif "verdict" in prompt_lower or "judgment" in prompt_lower:
                return json.dumps(
                    {
                        "revised_reasoning": "Based on comprehensive analysis",
                        "final_judgment": "Interest-based lending is prohibited",
                        "total_score": 75,
                    }
                )
            else:
                # Correction or other
                return json.dumps(
                    {
                        "corrections": [],
                        "revised_reasoning": "No corrections needed",
                        "final_judgment": "Interest-based lending is prohibited",
                        "total_score": 75,
                    }
                )

        return mock_llm

    def test_pipeline_instantiation(self):
        """Test EvaluationPipeline can be instantiated with a mock LLM."""
        from al_furqan.engine.pipeline import (
            EvaluationPipeline,  # pylint: disable=import-outside-toplevel
        )

        mock_llm = self._make_mock_llm()
        pipeline = EvaluationPipeline(mock_llm)
        assert pipeline is not None
        assert pipeline.llm_call is mock_llm

    def test_pipeline_scan_phase(self):
        """Test the scan phase with a mock LLM."""
        from al_furqan.engine.pipeline import (
            EvaluationPipeline,  # pylint: disable=import-outside-toplevel
        )

        pipeline = EvaluationPipeline(self._make_mock_llm())
        result = pipeline.scan("Is interest-based lending just?")

        assert isinstance(result, dict)
        assert "primary_system" in result
        assert result["primary_system"] == "economic"
        logger.info("Scan phase returned: %s", result)

    def test_pipeline_mirror_phase(self):
        """Test the mirror phase with a mock LLM."""
        from al_furqan.engine.pipeline import (
            EvaluationPipeline,  # pylint: disable=import-outside-toplevel
        )

        pipeline = EvaluationPipeline(self._make_mock_llm())
        scan_result = {
            "primary_system": "economic",
            "friction_points": ["interest"],
            "consequences_short_term": ["profit"],
            "consequences_long_term": ["instability"],
        }
        result = pipeline.mirror("Is interest-based lending just?", scan_result)

        assert isinstance(result, dict)
        assert "gate_scores" in result
        logger.info("Mirror phase returned %d gate scores", len(result["gate_scores"]))
