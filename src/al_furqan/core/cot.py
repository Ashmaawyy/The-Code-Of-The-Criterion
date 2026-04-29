"""
Al-Furqan COT (Chain of Thought) Module

Implements step-level reasoning for gates and a COT monitor
that validates reasoning chain integrity.

Based on: "Chain of Thought Monitorability: A New and Fragile
Opportunity for AI Safety" (Korbak et al., 2025)
"""

from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger("al_furqan.core.cot")


@dataclass
class ReasoningStep:
    """A single step in a chain of thought."""

    step_number: int
    thought: str  # What the model is thinking
    observation: str  # What it observes/finds
    axiom_reference: Optional[str] = None  # Which axiom this relates to
    conclusion: Optional[str] = None  # Only on final step

    def to_dict(self) -> dict:
        """Execute to_dict."""
        d = {
            "step_number": self.step_number,
            "thought": self.thought,
            "observation": self.observation,
        }
        if self.axiom_reference:
            d["axiom_reference"] = self.axiom_reference
        if self.conclusion:
            d["conclusion"] = self.conclusion
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ReasoningStep":
        """Execute from_dict."""
        return cls(
            step_number=d.get("step_number", 0),
            thought=d.get("thought", ""),
            observation=d.get("observation", ""),
            axiom_reference=d.get("axiom_reference"),
            conclusion=d.get("conclusion"),
        )


@dataclass
class COTMonitorResult:
    """Result from the COT monitor analyzing a reasoning chain."""

    trust_score: float  # 0.0 to 1.0
    flagged_steps: list[int]  # step numbers that are suspicious
    issues: list[str]  # descriptions of detected issues
    gate_gaming_detected: bool = False
    step_conclusion_consistent: bool = True
    axiom_compliance: bool = True

    def to_dict(self) -> dict:
        """Execute to_dict."""
        return {
            "trust_score": self.trust_score,
            "flagged_steps": self.flagged_steps,
            "issues": self.issues,
            "gate_gaming_detected": self.gate_gaming_detected,
            "step_conclusion_consistent": self.step_conclusion_consistent,
            "axiom_compliance": self.axiom_compliance,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "COTMonitorResult":
        """Execute from_dict."""
        return cls(
            trust_score=d.get("trust_score", 0.0),
            flagged_steps=d.get("flagged_steps", []),
            issues=d.get("issues", []),
            gate_gaming_detected=d.get("gate_gaming_detected", False),
            step_conclusion_consistent=d.get("step_conclusion_consistent", True),
            axiom_compliance=d.get("axiom_compliance", True),
        )
