"""
Shared fixtures for Al-Furqan unit tests.
"""

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to path so imports resolve
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from reasoning_engine import (
    Verdict,
    GateScore,
    GateResult,
    SystemType,
    ReasoningEngine,
)
from verdict_store import VerdictStore
from llm_layer import LLMConfig, OllamaProvider, LLMProvider


# ---------------------------------------------------------------------------
# Mock LLM Responses
# ---------------------------------------------------------------------------

MOCK_SCAN_RESPONSE = json.dumps({
    "primary_system": "economic",
    "immediate_effects": ["Wealth concentration", "Debt accumulation"],
    "network_effects": ["Systemic inequality", "Erosion of social trust"],
    "friction_points": [
        "Interest-based lending contradicts equitable wealth distribution",
        "Debt compounding violates network effect axiom",
    ],
})

MOCK_MIRROR_RESPONSE = json.dumps({
    "gate_1_source_integrity": {
        "score": 85,
        "result": "Survive",
        "reasoning": "Data on interest-based lending effects is well-documented.",
    },
    "gate_2_structural_consistency": {
        "score": 70,
        "result": "Survive",
        "reasoning": "Causal chain from interest to inequality is traceable.",
    },
    "gate_3_mediation_zeroing": {
        "score": 90,
        "result": "Survive",
        "reasoning": "Analysis does not rely on human preference as foundation.",
    },
    "gate_4_origin_aware": {
        "score": 80,
        "result": "Survive",
        "reasoning": "Prohibition of interest is derived from transcendent source.",
    },
    "contradictions_found": [],
    "axiom_alignment_notes": "Fully aligned with core axioms.",
})

MOCK_VERDICT_RESPONSE = json.dumps({
    "consequences_short_term": ["Increased household debt", "Reduced savings"],
    "consequences_long_term": ["Widening wealth gap", "Social instability"],
    "actors_and_mechanisms": "Lenders profit; borrowers bear compounding risk.",
    "revised_reasoning": "Interest-based lending creates systemic debt traps.",
    "final_judgment": "Interest-based lending violates design principles of equitable exchange.",
    "total_score": 85,
})

MOCK_CORRECTION_SOUND = json.dumps({
    "contradictions_found": [],
    "is_sound": True,
    "corrected_verdict": None,
})

MOCK_CORRECTION_WITH_FIX = json.dumps({
    "contradictions_found": ["Score should be higher given full gate survival"],
    "is_sound": False,
    "corrected_verdict": {
        "consequences_short_term": ["Increased household debt", "Reduced savings"],
        "consequences_long_term": ["Widening wealth gap", "Social instability"],
        "actors_and_mechanisms": "Lenders profit; borrowers bear compounding risk.",
        "revised_reasoning": "Interest-based lending creates systemic debt traps.",
        "final_judgment": "Interest-based lending violates design principles of equitable exchange.",
        "total_score": 90,
    },
})


def make_mock_llm(responses: list[str] | None = None):
    """
    Create a mock LLM callable that returns predefined responses in sequence.
    If no responses given, uses the default Scan → Mirror → Verdict → Correction flow.
    """
    if responses is None:
        responses = [
            MOCK_SCAN_RESPONSE,
            MOCK_MIRROR_RESPONSE,
            MOCK_VERDICT_RESPONSE,
            MOCK_CORRECTION_SOUND,
        ]
    call_count = {"n": 0}

    def mock_llm(prompt: str) -> str:
        idx = min(call_count["n"], len(responses) - 1)
        call_count["n"] += 1
        return responses[idx]

    return mock_llm


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_llm():
    """Default mock LLM that returns a full Scan→Mirror→Verdict→Correction flow."""
    return make_mock_llm()


@pytest.fixture
def engine(mock_llm):
    """ReasoningEngine wired to a mock LLM."""
    return ReasoningEngine(mock_llm)


@pytest.fixture
def sample_verdict():
    """A fully populated Verdict object for testing."""
    return Verdict(
        question="Is interest-based lending just?",
        primary_system=SystemType.ECONOMIC,
        friction_points=[
            "Interest contradicts equitable exchange",
            "Debt compounding harms borrowers",
        ],
        gate_scores=[
            GateScore("Source-Integrity", 85, GateResult.SURVIVE, "Data is well-documented."),
            GateScore("Structural-Consistency", 70, GateResult.SURVIVE, "Causal chain traceable."),
            GateScore("Mediation-Zeroing", 90, GateResult.SURVIVE, "No human preference reliance."),
        ],
        origin_gate=GateResult.SURVIVE,
        consequences_short_term=["Increased debt", "Reduced savings"],
        consequences_long_term=["Wealth gap", "Instability"],
        revised_reasoning="Interest creates systemic debt traps.",
        final_judgment="Interest-based lending violates equitable exchange.",
        total_score=85,
        passes=1,
        timestamp=1700000000.0,
    )


@pytest.fixture
def tmp_store(tmp_path):
    """A VerdictStore using temporary directories."""
    return VerdictStore(
        chroma_dir=tmp_path / "chroma",
        verdicts_dir=tmp_path / "verdicts",
    )
