"""
Gate 3: Mediation Zeroing (الوساطة) — Human Noise Audit

Evaluates whether the framework treats humans as observers of truth, not masters.

Scoring:
  - Foundation: non_human_foundation=90, mixed_foundation=50, pure_human_preference=20
  - removes_bias: +10
  - cultural_relativism: -30
  - Score clamped to [0, 100]
  - Survive threshold: score >= 50
"""

from al_furqan.engine.gates.base import Gate
from al_furqan.engine.models import GateScore, GateResult


FOUNDATION_SCORES = {
    "non_human_foundation": 90,
    "mixed_foundation": 50,
    "pure_human_preference": 20,
}

REMOVES_BIAS_BONUS = 10
CULTURAL_RELATIVISM_PENALTY = -30
SURVIVE_THRESHOLD = 50


class MediationZeroingGate(Gate):
    """Gate 3: Mediation Zeroing — audits human noise in truth claims."""

    @property
    def name(self) -> str:
        return "Mediation Zeroing (الوساطة)"

    @property
    def description(self) -> str:
        return (
            "Human cognition is contingent, finite, historically variable; "
            "therefore it cannot produce ultimate truth. Treat humans as "
            "observers of truth, not masters of it."
        )

    def get_chain_questions(self) -> list[str]:
        return [
            "Is this system founded on human preference, evolutionary ethics, or secular humanism — or on principles external to human cognition? Classify as: non_human_foundation, mixed_foundation, or pure_human_preference.",  # pylint: disable=line-too-long
            "Does the system rely on external, non-contingent principles (e.g., divine command, natural law from transcendent source)?",  # pylint: disable=line-too-long
            "Does the framework actively remove or account for human cognitive bias in its conclusions?",  # pylint: disable=line-too-long
            "Does the system embrace cultural relativism — treating truth as variable across cultures or time periods?",  # pylint: disable=line-too-long
        ]

    def evaluate(self, chain_results: dict) -> GateScore:
        """
        Deterministic scoring based on extracted facts.

        Expected chain_results keys:
            - foundation_type: str — non_human_foundation/mixed_foundation/pure_human_preference
            - removes_bias: bool
            - cultural_relativism: bool
        """
        foundation_type = (
            str(chain_results.get("foundation_type", "pure_human_preference"))
            .lower()
            .strip()
        )  # pylint: disable=line-too-long
        removes_bias = bool(chain_results.get("removes_bias", False))
        cultural_relativism = bool(chain_results.get("cultural_relativism", False))

        # Base score
        base_score = FOUNDATION_SCORES.get(
            foundation_type, FOUNDATION_SCORES["pure_human_preference"]
        )  # pylint: disable=line-too-long

        score = base_score

        # Adjustments
        if removes_bias:
            score += REMOVES_BIAS_BONUS
        if cultural_relativism:
            score += CULTURAL_RELATIVISM_PENALTY

        # Clamp
        score = max(0, min(100, score))

        result = GateResult.SURVIVE if score >= SURVIVE_THRESHOLD else GateResult.FAIL

        reasoning_parts = [
            f"Foundation type: {foundation_type} (base={base_score})",
            f"Removes bias: {removes_bias} ({'+' if removes_bias else ''}{REMOVES_BIAS_BONUS if removes_bias else 0})",  # pylint: disable=line-too-long
            f"Cultural relativism: {cultural_relativism} ({CULTURAL_RELATIVISM_PENALTY if cultural_relativism else 0})",  # pylint: disable=line-too-long
            f"Final score: {score}/100 → {result.value}",
        ]

        return GateScore(
            name=self.name,
            score=score,
            result=result,
            reasoning="; ".join(reasoning_parts),
        )
