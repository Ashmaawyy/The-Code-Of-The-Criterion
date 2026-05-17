"""
Gate 5: Origin Preservation (الحفظ) — Reference Source Preservance

Evaluates whether the framework has been preserved over time without mutations in core principles.

Scoring:
  - preservation_status: preserved=100, minor_drift=60, significant_mutations=20
  - core_principles_intact: +10
  - functionality_manual_aligned: +10
  - core_mutated: -50
  - Score clamped to [0, 100]
  - Survive threshold: score >= 50
"""

from al_furqan.engine.gates.base import Gate
from al_furqan.engine.models import GateScore, GateResult


PRESERVATION_SCORES = {
    "preserved": 100,
    "minor_drift": 60,
    "significant_mutations": 20,
}

CORE_PRINCIPLES_INTACT_BONUS = 10
FUNCTIONALITY_MANUAL_ALIGNED_BONUS = 10
CORE_MUTATED_PENALTY = -50
SURVIVE_THRESHOLD = 50


class OriginPreservationGate(Gate):
    """Gate 5: Origin Preservation — evaluates temporal consistency of framework."""

    @property
    def name(self) -> str:
        return "Origin Preservation (الحفظ)"

    @property
    def description(self) -> str:
        return (
            "Is the framework preserved over time without mutations in its core principles? "
            "The framework must maintain fidelity to its foundational claims across time."
        )

    def get_chain_questions(self) -> list[str]:
        return [
            "Has this framework been preserved over time, or has it undergone mutations in its core principles? Classify as: preserved, minor_drift, or significant_mutations.",  # pylint: disable=line-too-long
            "Are the core principles of this framework intact across historical implementations or versions?",  # pylint: disable=line-too-long
            "Does the framework's functionality manual (if it exists) remain aligned with its core principles?",  # pylint: disable=line-too-long
            "Have there been any mutations or corruptions introduced into the framework's foundational claims over time?",  # pylint: disable=line-too-long
            "Can the framework demonstrate an unbroken chain of transmission or preservation of its core doctrines?",  # pylint: disable=line-too-long
        ]

    def evaluate(self, chain_results: dict) -> GateScore:
        """
        Deterministic scoring based on extracted facts.

        Expected chain_results keys:
            - preservation_status: str — preserved/minor_drift/significant_mutations
            - core_principles_intact: bool
            - functionality_manual_aligned: bool
            - core_mutated: bool
        """
        preservation_status = (
            str(chain_results.get("preservation_status", "significant_mutations"))
            .lower()
            .strip()
        )
        core_principles_intact = bool(chain_results.get("core_principles_intact", False))
        functionality_manual_aligned = bool(
            chain_results.get("functionality_manual_aligned", False)
        )
        core_mutated = bool(chain_results.get("core_mutated", False))

        # Base score from preservation status
        base_score = PRESERVATION_SCORES.get(
            preservation_status, PRESERVATION_SCORES["significant_mutations"]
        )

        score = base_score

        # Adjustments
        if core_principles_intact:
            score += CORE_PRINCIPLES_INTACT_BONUS
        if functionality_manual_aligned:
            score += FUNCTIONALITY_MANUAL_ALIGNED_BONUS
        if core_mutated:
            score += CORE_MUTATED_PENALTY

        # Clamp
        score = max(0, min(100, score))

        result = GateResult.SURVIVE if score >= SURVIVE_THRESHOLD else GateResult.FAIL

        reasoning_parts = [
            f"Preservation status: {preservation_status} (base={base_score})",
            f"Core principles intact: {core_principles_intact} ({'+' if core_principles_intact else ''}{CORE_PRINCIPLES_INTACT_BONUS if core_principles_intact else 0})",  # pylint: disable=line-too-long
            f"Functionality manual aligned: {functionality_manual_aligned} ({'+' if functionality_manual_aligned else ''}{FUNCTIONALITY_MANUAL_ALIGNED_BONUS if functionality_manual_aligned else 0})",  # pylint: disable=line-too-long
            f"Core mutated: {core_mutated} ({CORE_MUTATED_PENALTY if core_mutated else 0})",
            f"Final score: {score}/100 → {result.value}",
        ]

        return GateScore(
            name=self.name,
            score=score,
            result=result,
            reasoning="; ".join(reasoning_parts),
        )
