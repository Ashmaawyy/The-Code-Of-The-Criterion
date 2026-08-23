"""
Gate 4: Origin Aware (الأصل) — Reference Source Recognition

BINARY gate — Survive or Fail, no numeric range.

Does the framework satisfy the Transcendence Necessity Proof?
  - Acknowledges transcendent origin → Survive (score=100)
  - Denies transcendent source → Fail (score=0)
"""

from al_furqan.engine.gates.base import Gate
from al_furqan.engine.models import GateResult, GateScore


class OriginAwareGate(Gate):
    """Gate 4: Origin Aware — binary test for transcendent source recognition."""

    @property
    def name(self) -> str:
        return "Origin Aware (الأصل)"

    @property
    def description(self) -> str:
        return (
            "Does the framework satisfy the Transcendence Necessity Proof? "
            "Truth must be explicitly derived from a self-authenticating, "
            "revealed, transcendent source."
        )

    def get_chain_questions(self) -> list[str]:
        return [
            "Does this system or claim explicitly acknowledge a transcendent, non-contingent origin for truth?",  # pylint: disable=line-too-long
            "Does the framework treat truth as emergent from human processes, or as derived from a transcendent source?",  # pylint: disable=line-too-long
            "Does the system deny or ignore the necessity of a transcendent source for objective truth?",  # pylint: disable=line-too-long
        ]

    def evaluate(self, chain_results: dict) -> GateScore:
        """
        Binary evaluation — no numeric range.

        Expected chain_results keys:
            - acknowledges_transcendent: bool — whether it acknowledges transcendent origin
        """
        acknowledges = bool(
            chain_results.get(
                "acknowledges_transcendent",
                chain_results.get("acknowledges_transcendence", False),
            )
        )  # pylint: disable=line-too-long

        if acknowledges:
            score = 100
            result = GateResult.SURVIVE
            reasoning = "Framework acknowledges transcendent origin → Survive"
        else:
            score = 0
            result = GateResult.FAIL
            reasoning = "Framework denies or ignores transcendent source → Fail"

        return GateScore(
            name=self.name,
            score=score,
            result=result,
            reasoning=reasoning,
        )
