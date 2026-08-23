"""
Al-Furqan Engine — The Criterion

Public API for the engine package. All symbols that were previously
available from core.reasoning_engine are re-exported here for
backward compatibility.
"""

from al_furqan.engine.axioms import (
    AXIOM_HASH,
    AXIOM_VERSION,
    AXIOMS,
    FRAMEWORK_PREAMBLE,
    GATE_DEFINITIONS,
    SCORING_RULES,
)
from al_furqan.engine.models import (
    DualPerspectiveVerdict,
    GateResult,
    GateScore,
    InformationalResponse,
    SystemType,
    Verdict,
)
from al_furqan.engine.pipeline import EvaluationPipeline
from al_furqan.engine.prompts import (
    MAX_QUESTION_LENGTH,
    build_correction_prompt,
    build_informational_prompt,
    build_intent_detection_prompt,
    build_mirror_prompt,
    build_scan_prompt,
    build_verdict_prompt,
    sanitize_input,
)

__all__ = [
    # Axioms
    "AXIOM_HASH",
    "AXIOM_VERSION",
    "AXIOMS",
    "FRAMEWORK_PREAMBLE",
    "GATE_DEFINITIONS",
    "SCORING_RULES",
    # Models
    "DualPerspectiveVerdict",
    "GateResult",
    "GateScore",
    "InformationalResponse",
    "SystemType",
    "Verdict",
    # Pipeline
    "EvaluationPipeline",
    # Prompts
    "build_correction_prompt",
    "build_informational_prompt",
    "build_intent_detection_prompt",
    "build_mirror_prompt",
    "build_scan_prompt",
    "build_verdict_prompt",
    "sanitize_input",
    "MAX_QUESTION_LENGTH",
]
