"""
Deterministic Scorer — Pure Python scoring, NO LLM involvement.

Takes extracted facts and applies deterministic rules through each gate's
evaluate() method. Same input ALWAYS produces the same output.
"""

from al_furqan.engine.gates.base import Gate
from al_furqan.engine.models import GateScore


class DeterministicScorer:
    """
    Pure Python scoring engine.

    No LLM calls — takes extracted facts and computes scores
    deterministically through gate evaluate() methods.
    """

    def score_gate(self, gate: Gate, extractions: dict) -> GateScore:
        """
        Score a single gate with extracted facts.

        Args:
            gate: The Gate instance to score.
            extractions: Dictionary of extracted facts for this gate.

        Returns:
            GateScore with deterministic result.
        """
        return gate.evaluate(extractions)

    def score_all_gates(
        self,
        gates: list[Gate],
        all_extractions: dict,
    ) -> list[GateScore]:
        """
        Score all gates deterministically.

        Args:
            gates: List of Gate instances.
            all_extractions: Dictionary mapping gate names to their extractions.

        Returns:
            List of GateScore results, one per gate.
        """
        results = []
        for gate in gates:
            gate_extractions = all_extractions.get(gate.name, {})
            score = self.score_gate(gate, gate_extractions)
            results.append(score)
        return results

    def compute_total_score(self, gate_scores: list[GateScore]) -> int:
        """
        Compute total score across all gates.

        Returns average of all gate scores, clamped to [0, 100].
        """
        if not gate_scores:
            return 0
        total = sum(gs.score for gs in gate_scores)
        return max(0, min(100, total // len(gate_scores)))
