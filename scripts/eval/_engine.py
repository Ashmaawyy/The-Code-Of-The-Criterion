"""Shared helpers for Al-Furqan eval scripts.

Centralises the LLM-response cleaning, gate scoring, Z3 verification, and
logging that every eval_* script used to copy-paste. Each eval script should
still own its question text and prompt wording; only the downstream plumbing
belongs here.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Make al_furqan importable regardless of CWD
_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from al_furqan.engine.gates import (  # noqa: E402
    MediationZeroingGate,
    OriginAwareGate,
    SourceIntegrityGate,
    StructuralConsistencyGate,
)
from al_furqan.engine.symbolic.verifier import SymbolicVerifier  # noqa: E402
from al_furqan.providers.llm_layer import LLMConfig, create_llm  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen3.5-397b-a17b"

_GATES: tuple | None = None
_VERIFIER: SymbolicVerifier | None = None


def _ensure_gates():
    global _GATES, _VERIFIER  # pylint: disable=global-statement
    if _GATES is None:
        _GATES = (
            SourceIntegrityGate(),
            StructuralConsistencyGate(),
            MediationZeroingGate(),
            OriginAwareGate(),
        )
    if _VERIFIER is None:
        _VERIFIER = SymbolicVerifier()
    return _GATES, _VERIFIER


def get_api_key() -> str:
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        raise SystemExit("DASHSCOPE_API_KEY environment variable not set")
    return api_key


def make_llm(model: str = DEFAULT_MODEL, temperature: float = 0.1, max_tokens: int = 4000):
    config = LLMConfig(
        provider="dashscope",
        model_name=model,
        api_key=get_api_key(),
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return create_llm(config)


def clean_llm_output(raw: str) -> tuple[str, str]:
    """Strip ``<think>`` blocks and code fences. Returns ``(clean, thinking)``."""
    clean = raw.strip()
    thinking = ""
    if "<think>" in clean:
        ts = clean.index("<think>")
        te = clean.find("</think>")
        if te > 0:
            thinking = clean[ts + 7 : te].strip()
            clean = clean[te + 8 :].strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:-1]).strip()
    return clean, thinking


def parse_json_from_llm(raw: str) -> dict[str, Any]:
    clean, _ = clean_llm_output(raw)
    if "{" not in clean:
        raise ValueError(f"No JSON found in LLM output: {clean[:200]}")
    return json.loads(clean[clean.index("{") : clean.rindex("}") + 1])


@dataclass
class GateScores:
    g1_score: int
    g2_score: int
    g3_score: int
    g4_result: str
    avg: int
    all_survive: bool
    z3_consistent: bool
    z3_proof: str


def score_entity(entity_data: dict[str, Any]) -> GateScores:
    """Run all 4 gates + Z3 on a single entity dict."""
    (g1, g2, g3, g4), verifier = _ensure_gates()
    s1 = g1.evaluate(entity_data)
    s2 = g2.evaluate(entity_data)
    s3 = g3.evaluate(entity_data)
    s4 = g4.evaluate(entity_data)
    avg = (s1.score + s2.score + s3.score) // 3
    all_survive = all(s.result.value == "Survive" for s in (s1, s2, s3, s4))

    z = verifier.verify_verdict({
        "source_type": entity_data.get("source_type", ""),
        "has_contradictions": entity_data.get("contradicts_primary", False),
        "relies_on_human_preference":
            entity_data.get("foundation_type", "") == "pure_human_preference",
        "acknowledges_transcendence": entity_data.get("acknowledges_transcendence", False),
        "exists": True,
        "has_purpose": True,
        "is_contingent": entity_data.get("source_type", "") == "human_theory",
        "has_transcendent_source": entity_data.get("acknowledges_transcendence", False),
    })

    return GateScores(
        g1_score=s1.score,
        g2_score=s2.score,
        g3_score=s3.score,
        g4_result=s4.result.value,
        avg=avg,
        all_survive=all_survive,
        z3_consistent=z.consistent,
        z3_proof=z.proof,
    )


def log_gate_scores(label: str, scores: GateScores, reasoning: str = "") -> None:
    status = "ALL SURVIVE" if scores.all_survive else "FAIL"
    logger.info("--- %s ---", label)
    logger.info("  Gate 1 (Source Integrity):       %3d/100", scores.g1_score)
    logger.info("  Gate 2 (Structural Consistency): %3d/100", scores.g2_score)
    logger.info("  Gate 3 (Mediation Zeroing):      %3d/100", scores.g3_score)
    logger.info("  Gate 4 (Origin Aware):           %s", scores.g4_result)
    logger.info("  Average: %d/100 - %s", scores.avg, status)
    logger.info("  Z3: consistent=%s", scores.z3_consistent)
    if reasoning:
        logger.info("  Reasoning: %s", reasoning[:200])


def log_thinking(thinking: str, char_limit: int = 800) -> None:
    if not thinking:
        return
    logger.info("  [THINKING] (%d chars):", len(thinking))
    for line in thinking[:char_limit].split("\n"):
        logger.info("    %s", line)
    if len(thinking) > char_limit:
        logger.info("    ... (truncated)")


def log_json(clean_text: str) -> None:
    logger.info("  [JSON OUTPUT]:")
    for line in clean_text.split("\n"):
        logger.info("    %s", line)


def log_response(body: str, indent: str = "  ") -> None:
    for line in body.split("\n"):
        logger.info("%s%s", indent, line)


def strip_thinking(raw: str) -> str:
    """Return LLM output with any ``<think>`` block removed (no code-fence strip)."""
    clean = raw.strip()
    if "<think>" in clean:
        te = clean.find("</think>")
        if te > 0:
            clean = clean[te + 8 :].strip()
    return clean
