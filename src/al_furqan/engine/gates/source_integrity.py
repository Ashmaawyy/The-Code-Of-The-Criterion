"""
Gate 1: Source Integrity (المصدر) — Data Fidelity

Evaluates the origin and verifiability of claims.
Preserve raw truth. Require logical proof backed by evidence.

Scoring:
  - Source type: divine=90, prophetic=80, scholarly=60, human_theory=40, unknown=20
  - Verifiability multiplier: verifiable ×1.0, unverifiable ×0.5
  - Contradicts primary sources: -40
  - Score clamped to [0, 100]
  - Survive threshold: score >= 50
"""

from al_furqan.engine.gates.base import Gate
from al_furqan.engine.models import GateScore, GateResult


# Deterministic score map for source types
SOURCE_TYPE_SCORES = {
    "divine": 100,
    "prophetic": 80,
    "scholarly": 60,
    "human_theory": 40,
    "unknown": 20,
}

VERIFIABLE_MULTIPLIER = 1.0
UNVERIFIABLE_MULTIPLIER = 0.5
CONTRADICTS_PRIMARY_PENALTY = -40
SURVIVE_THRESHOLD = 50


class SourceIntegrityGate(Gate):
    """Gate 1: Source Integrity — evaluates data fidelity and source origin."""

    @property
    def name(self) -> str:
        return "Source Integrity (المصدر)"

    @property
    def description(self) -> str:
        return (
            "Preserve raw truth. Require logical proof backed by evidence "
            "in reality for any human-made claim, or require proof from a "
            "transcendent non-contingent source."
        )

    def get_chain_questions(self) -> list[str]:
        return [
            "What is the primary source of this claim or system? (divine revelation, prophetic tradition, scholarly consensus, human theory, or unknown)",  # pylint: disable=line-too-long
            "Is the source verifiable through established chains of transmission, empirical evidence, or logical proof?",  # pylint: disable=line-too-long
            "Does the claim classify as divine, prophetic, scholarly, human_theory, or unknown in origin?",  # pylint: disable=line-too-long
            "Does this claim contradict any established primary sources (Quran, authenticated Hadith)?",  # pylint: disable=line-too-long
            "Is there any reduction, omission, or reinterpretation of established truths for human convenience?",  # pylint: disable=line-too-long
        ]

    def evaluate(self, chain_results: dict) -> GateScore:
        """
        Deterministic scoring based on extracted facts.

        Expected chain_results keys:
            - source_type: str — one of divine/prophetic/scholarly/human_theory/unknown
            - verifiable: bool — whether the source is verifiable
            - contradicts_primary: bool — whether it contradicts primary sources
        """
        source_type = str(chain_results.get("source_type", "unknown")).lower().strip()
        verifiable = bool(
            chain_results.get("verifiable", chain_results.get("is_verifiable", False))
        )  # pylint: disable=line-too-long
        contradicts_primary = bool(chain_results.get("contradicts_primary", False))

        # Base score from source type
        base_score = SOURCE_TYPE_SCORES.get(source_type, SOURCE_TYPE_SCORES["unknown"])

        # Verifiability multiplier
        multiplier = VERIFIABLE_MULTIPLIER if verifiable else UNVERIFIABLE_MULTIPLIER
        score = int(base_score * multiplier)

        # Contradiction penalty
        if contradicts_primary:
            score += CONTRADICTS_PRIMARY_PENALTY

        # Clamp
        score = max(0, min(100, score))

        # Determine result
        result = GateResult.SURVIVE if score >= SURVIVE_THRESHOLD else GateResult.FAIL

        # Build reasoning
        reasoning_parts = [
            f"Source type: {source_type} (base={base_score})",
            f"Verifiable: {verifiable} (×{multiplier})",
        ]
        if contradicts_primary:
            reasoning_parts.append(
                f"Contradicts primary sources: penalty {CONTRADICTS_PRIMARY_PENALTY}"
            )  # pylint: disable=line-too-long
        reasoning_parts.append(f"Final score: {score}/100 → {result.value}")

        return GateScore(
            name=self.name,
            score=score,
            result=result,
            reasoning="; ".join(reasoning_parts),
        )
