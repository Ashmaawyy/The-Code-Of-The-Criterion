"""
Al-Furqan Reasoning Engine — The Criterion

This module is a backward-compatible wrapper. All implementations have been
extracted to the ``al_furqan.engine`` package (Sprint 3A refactor).

Imports from this module still work — they are re-exported from their
new canonical locations:
  - axioms   → al_furqan.engine.axioms
  - models   → al_furqan.engine.models
  - prompts  → al_furqan.engine.prompts
  - pipeline → al_furqan.engine.pipeline
"""

# pylint: disable=unused-import
# pylint: disable=unnecessary-pass

# ---------------------------------------------------------------------------
# Re-exports: Axioms
# ---------------------------------------------------------------------------
from al_furqan.engine.axioms import (  # noqa: F401
    AXIOM_HASH,
    AXIOM_VERSION,
    AXIOMS,
    EVALUATION_QUESTIONS,
    FRAMEWORK_PREAMBLE,
    GATE_DEFINITIONS,
    OPERATIONAL_NOTES,
    SCORING_RULES,
    SEALED_AXIOM_HASH,
)

# ---------------------------------------------------------------------------
# Re-exports: Models
# ---------------------------------------------------------------------------
from al_furqan.engine.models import (  # noqa: F401
    DualPerspectiveVerdict,
    GateResult,
    GateScore,
    InformationalResponse,
    SystemType,
    Verdict,
)

# ---------------------------------------------------------------------------
# Re-exports: Prompts & Sanitization
# ---------------------------------------------------------------------------
from al_furqan.engine.prompts import (  # noqa: F401
    MAX_QUESTION_LENGTH,
    build_correction_prompt,
    build_informational_prompt,
    build_intent_detection_prompt,
    build_mirror_prompt,
    build_scan_prompt,
    build_verdict_prompt,
    sanitize_input,
)

# ---------------------------------------------------------------------------
# Re-exports: Pipeline (as EvaluationPipeline)
# ---------------------------------------------------------------------------
from al_furqan.engine.pipeline import EvaluationPipeline  # noqa: F401


# ---------------------------------------------------------------------------
# ReasoningEngine — thin wrapper around EvaluationPipeline
# ---------------------------------------------------------------------------
class ReasoningEngine(EvaluationPipeline):
    """
    The Criterion reasoning engine.

    Backward-compatible wrapper around EvaluationPipeline.
    All logic lives in al_furqan.engine.pipeline.EvaluationPipeline.
    """

    pass
