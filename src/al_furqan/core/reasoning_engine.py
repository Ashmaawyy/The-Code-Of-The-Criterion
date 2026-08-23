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

# ---------------------------------------------------------------------------
# Re-exports: Models
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Re-exports: Pipeline (as EvaluationPipeline)
# ---------------------------------------------------------------------------
from al_furqan.engine.pipeline import EvaluationPipeline

# ---------------------------------------------------------------------------
# Re-exports: Prompts & Sanitization
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# ReasoningEngine — thin wrapper around EvaluationPipeline
# ---------------------------------------------------------------------------
class ReasoningEngine(EvaluationPipeline):
    """
    The Criterion reasoning engine.

    Backward-compatible wrapper around EvaluationPipeline.
    All logic lives in al_furqan.engine.pipeline.EvaluationPipeline.
    """
