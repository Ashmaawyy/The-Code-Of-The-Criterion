"""
Al-Furqan Data Models

Core data structures for the reasoning engine: SystemType, GateResult,
GateScore, Verdict, DualPerspectiveVerdict, InformationalResponse.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SystemType(Enum):
    """SystemType class."""

    ECONOMIC = "economic"
    SOCIAL = "social"
    SPIRITUAL = "spiritual"
    POLITICAL = "political"
    LEGAL = "legal"
    TECHNOLOGICAL = "technological"
    ENVIRONMENTAL = "environmental"
    MIXED = "mixed"


class GateResult(Enum):
    """GateResult class."""

    SURVIVE = "Survive"
    FAIL = "Fail"


# ---------------------------------------------------------------------------
# Gate Score
# ---------------------------------------------------------------------------


@dataclass
class GateScore:
    """GateScore class."""

    name: str
    score: int  # 0-100
    result: GateResult
    reasoning: str

    def to_dict(self) -> dict:
        """Execute to_dict."""
        return {
            "name": self.name,
            "score": self.score,
            "result": self.result.value,
            "reasoning": self.reasoning,
        }


# ---------------------------------------------------------------------------
# Verdict (3A.4 — with model metadata fields)
# ---------------------------------------------------------------------------


@dataclass
class Verdict:  # pylint: disable=too-many-instance-attributes
    """Verdict class."""

    question: str
    primary_system: SystemType
    friction_points: list[str]
    gate_scores: list[GateScore]
    origin_gate: GateResult
    consequences_short_term: list[str]
    consequences_long_term: list[str]
    revised_reasoning: str
    final_judgment: str
    total_score: int
    passes: int  # how many self-correction passes were run
    timestamp: float = field(default_factory=time.time)
    # 3A.4 — Model metadata
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    model_temperature: Optional[float] = None
    raw_scan_response: Optional[str] = None
    raw_mirror_response: Optional[str] = None
    raw_verdict_response: Optional[str] = None

    def to_log(self) -> str:
        """Return a human-readable string representation of the verdict."""
        lines = [
            "=== VERDICT ===",
            f"Question: {self.question}",
            f"Primary System Identified: {self.primary_system.value}",
            "",
        ]

        if self.friction_points:
            lines.append("Friction Points:")
            for fp in self.friction_points:
                lines.append(f"  - {fp}")
            lines.append("")

        lines.append("Gate Scores:")
        for gs in self.gate_scores:
            lines.append(f"  {gs.name}: {gs.score}/100 [{gs.result.value}]")
            if gs.reasoning:
                lines.append(f"    Reasoning: {gs.reasoning}")
        lines.append("")

        lines.append(f"Origin-Aware Gate: {self.origin_gate.value}")
        lines.append("")

        if self.consequences_short_term:
            lines.append("Short-Term Consequences:")
            for c in self.consequences_short_term:
                lines.append(f"  - {c}")

        if self.consequences_long_term:
            lines.append("Long-Term Consequences:")
            for c in self.consequences_long_term:
                lines.append(f"  - {c}")

        lines.append("")
        lines.append(f"Revised Reasoning: {self.revised_reasoning}")
        lines.append(f"Final Judgment: {self.final_judgment}")
        lines.append(f"Total Score: {self.total_score}")
        lines.append(f"Correction Passes: {self.passes}")

        if self.model_name:
            lines.append(f"Model: {self.model_name}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Execute to_dict."""
        d = {
            "question": self.question,
            "primary_system": self.primary_system.value,
            "friction_points": self.friction_points,
            "gate_scores": [g.to_dict() for g in self.gate_scores],
            "origin_gate": self.origin_gate.value,
            "consequences_short_term": self.consequences_short_term,
            "consequences_long_term": self.consequences_long_term,
            "revised_reasoning": self.revised_reasoning,
            "final_judgment": self.final_judgment,
            "total_score": self.total_score,
            "passes": self.passes,
            "timestamp": self.timestamp,
        }
        # 3A.4 — Include model metadata if present
        if self.model_provider is not None:
            d["model_provider"] = self.model_provider
        if self.model_name is not None:
            d["model_name"] = self.model_name
        if self.model_temperature is not None:
            d["model_temperature"] = self.model_temperature
        if self.raw_scan_response is not None:
            d["raw_scan_response"] = self.raw_scan_response
        if self.raw_mirror_response is not None:
            d["raw_mirror_response"] = self.raw_mirror_response
        if self.raw_verdict_response is not None:
            d["raw_verdict_response"] = self.raw_verdict_response
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Verdict":
        """Reconstruct a Verdict from a dictionary (e.g., loaded from JSON)."""
        gate_scores = [
            GateScore(
                name=g["name"],
                score=int(g.get("score", 0)),
                result=GateResult.SURVIVE
                if g.get("result") == "Survive"
                else GateResult.FAIL,
                reasoning=g.get("reasoning", ""),
            )
            for g in d.get("gate_scores", [])
        ]
        try:
            system_type = SystemType(d.get("primary_system", "mixed"))
        except ValueError:
            system_type = SystemType.MIXED
        origin_str = d.get("origin_gate", "Fail")
        origin_gate = GateResult.SURVIVE if origin_str == "Survive" else GateResult.FAIL
        return cls(
            question=d.get("question", ""),
            primary_system=system_type,
            friction_points=d.get("friction_points", []),
            gate_scores=gate_scores,
            origin_gate=origin_gate,
            consequences_short_term=d.get("consequences_short_term", []),
            consequences_long_term=d.get("consequences_long_term", []),
            revised_reasoning=d.get("revised_reasoning", ""),
            final_judgment=d.get("final_judgment", ""),
            total_score=int(d.get("total_score", 0)),
            passes=int(d.get("passes", 0)),
            timestamp=d.get("timestamp", 0.0),
            # 3A.4 — Model metadata
            model_provider=d.get("model_provider"),
            model_name=d.get("model_name"),
            model_temperature=d.get("model_temperature"),
            raw_scan_response=d.get("raw_scan_response"),
            raw_mirror_response=d.get("raw_mirror_response"),
            raw_verdict_response=d.get("raw_verdict_response"),
        )


# ---------------------------------------------------------------------------
# Dual Perspective Verdict
# ---------------------------------------------------------------------------


@dataclass
class DualPerspectiveVerdict:
    """
    Dual-perspective evaluation result (Solution 3).

    Contains two verdicts:
    1. system_verdict: Evaluation of the target system/framework itself
    2. assumptions_verdict: Evaluation of the question's embedded assumptions
    Plus intent detection metadata.
    """

    intent_type: str  # "system_evaluation" or "claim_judgment"
    target_system: str
    embedded_assumptions: list[str]
    neutralized_question: str
    system_verdict: Verdict  # The main verdict on the system
    assumptions_verdict: Optional[
        Verdict
    ]  # Verdict on the question's assumptions (if any)

    def to_dict(self) -> dict:
        """Execute to_dict."""
        return {
            "dual_perspective": True,
            "intent_type": self.intent_type,
            "target_system": self.target_system,
            "embedded_assumptions": self.embedded_assumptions,
            "neutralized_question": self.neutralized_question,
            "system_verdict": self.system_verdict.to_dict(),
            "assumptions_verdict": self.assumptions_verdict.to_dict()
            if self.assumptions_verdict
            else None,  # pylint: disable=line-too-long
        }

    def to_log(self) -> str:
        """Execute to_log."""
        lines = [
            "=== DUAL-PERSPECTIVE EVALUATION ===",
            f"Intent: {self.intent_type}",
            f"Target System: {self.target_system}",
            f"Neutralized Q: {self.neutralized_question}",
            f"Embedded Assumptions: {'; '.join(self.embedded_assumptions)}",
            "",
            "--- SYSTEM VERDICT ---",
            self.system_verdict.to_log()
            if hasattr(self.system_verdict, "to_log")
            else str(self.system_verdict.to_dict()),  # pylint: disable=line-too-long
        ]
        if self.assumptions_verdict:
            lines += [
                "",
                "--- ASSUMPTIONS VERDICT ---",
                self.assumptions_verdict.to_log()
                if hasattr(self.assumptions_verdict, "to_log")
                else str(self.assumptions_verdict.to_dict()),  # pylint: disable=line-too-long
            ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Informational Response
# ---------------------------------------------------------------------------


@dataclass
class InformationalResponse:
    """Response for informational (non-evaluative) questions."""

    question: str
    answer: str
    category: str
    sources_suggested: list[str]
    related_topics: list[str]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Execute to_dict."""
        return {
            "informational": True,
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "sources_suggested": self.sources_suggested,
            "related_topics": self.related_topics,
            "timestamp": self.timestamp,
        }

    def to_log(self) -> str:
        """Execute to_log."""
        return (
            f"=== INFORMATIONAL RESPONSE ===\n"
            f"Question: {self.question}\n"
            f"Category: {self.category}\n"
            f"Answer: {self.answer[:500]}\n"
            f"Sources: {'; '.join(self.sources_suggested)}\n"
            f"Related: {'; '.join(self.related_topics)}"
        )
