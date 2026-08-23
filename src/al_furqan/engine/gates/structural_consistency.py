"""
Gate 2: Structural Consistency (البنية) — Causal Mapping

Evaluates internal logical consistency and causal chains.
Includes critical depth rule: applies foundationally via khalq → ṣūra → taqdīr → hidāya.

Scoring:
  - Contradiction level: no_contradictions=90, minor_inconsistencies=60, major_contradictions=30
  - causal_chain_intact: +10
  - logical_gaps: -20
  - depth_foundational: +20 (framework explains all 4 layers)
  - depth_borrowed (only hidāya layer): -50 (fails foundation)
  - Score clamped to [0, 100]
  - Survive threshold: score >= 50
"""

from al_furqan.engine.gates.base import Gate
from al_furqan.engine.models import GateResult, GateScore

CONTRADICTION_SCORES = {
    "no_contradictions": 90,
    "minor_inconsistencies": 60,
    "major_contradictions": 30,
}

CAUSAL_CHAIN_BONUS = 10
LOGICAL_GAPS_PENALTY = -20
DEPTH_FOUNDATIONAL_BONUS = 20  # Framework explains khalq→ṣūra→taqdīr→hidāya
DEPTH_BORROWED_PENALTY = -50  # Framework only operates at hidāya layer
SURVIVE_THRESHOLD = 50


class StructuralConsistencyGate(Gate):
    """Gate 2: Structural Consistency — evaluates causal mapping and logical coherence."""

    @property
    def name(self) -> str:
        return "Structural Consistency (البنية)"

    @property
    def description(self) -> str:
        return (
            "Can explain systemic stability, causality, and events without "
            "luck or emergent randomness. Link all events and patterns to a "
            "singular non-contingent source."
        )

    def get_chain_questions(self) -> list[str]:
        return [
            "Does this system or claim contain any internal contradictions? Classify as: no_contradictions, minor_inconsistencies, or major_contradictions.",  # pylint: disable=line-too-long
            "Is the causal chain intact — does every effect trace back to a clearly identified cause without appealing to luck or randomness?",  # pylint: disable=line-too-long
            "Are there logical gaps where conclusions are drawn without sufficient premises or evidence?",  # pylint: disable=line-too-long
            "Can the system explain its own stability and order without resorting to emergent randomness?",  # pylint: disable=line-too-long
            "DEPTH TEST: Does the framework explain the four-layer foundation? (khalq=creation of substance, ṣūra=assignment of form, taqdīr=decreed measure/invariances, hidāya=guided behavior/dynamics). Does it operate at all layers, or only at hidāya?",  # pylint: disable=line-too-long
            "If the framework operates only at the hidāya (behavior) layer, does it acknowledge or attempt to explain the three layers beneath it (khalq, ṣūra, taqdīr)?",  # pylint: disable=line-too-long
        ]

    def evaluate(self, chain_results: dict) -> GateScore:
        """
        Deterministic scoring based on extracted facts.

        Expected chain_results keys:
            - contradiction_level: str — no_contradictions/minor_inconsistencies/major_contradictions  # pylint: disable=line-too-long
            - causal_chain_intact: bool
            - logical_gaps: bool
            - depth_foundational: bool — framework explains all 4 layers (khalq→ṣūra→taqdīr→hidāya)
            - depth_borrowed_only_hidaya: bool — framework operates only at hidāya layer
        """
        contradiction_level = (
            str(
                chain_results.get(
                    "contradiction_level",
                    chain_results.get("consistency_level", "major_contradictions"),
                )
            )
            .lower()
            .strip()
        )  # pylint: disable=line-too-long
        causal_chain_intact = bool(chain_results.get("causal_chain_intact", False))
        logical_gaps = bool(
            chain_results.get(
                "logical_gaps", chain_results.get("has_logical_gaps", False)
            )
        )  # pylint: disable=line-too-long
        depth_foundational = bool(chain_results.get("depth_foundational", False))
        depth_borrowed_only_hidaya = bool(
            chain_results.get("depth_borrowed_only_hidaya", False)
        )

        # ── Divine Source Abrogation Check ──
        # If the source is divine and contains abrogation (nasikh/mansukh),
        # check whether the source ITSELF explains the abrogation.
        # A Designer explaining design changes ≠ contradiction.
        # A human source with contradictions = real contradiction.
        source_type = str(chain_results.get("source_type", "")).lower().strip()
        has_abrogation = bool(chain_results.get("has_abrogation", False))
        source_addresses_abrogation = bool(
            chain_results.get("source_addresses_abrogation", False)
        )

        if source_type == "divine" and has_abrogation:
            if source_addresses_abrogation:
                # The divine source explains why abrogation exists
                # (e.g., Quran 2:106 — "We do not abrogate a verse or cause
                # it to be forgotten except that We bring forth one better
                # than it or similar to it")
                # This is design by the Designer, not contradiction
                contradiction_level = "no_contradictions"
            else:
                # Divine source has abrogation but doesn't explain it
                # Treat as minor — needs further scholarly review
                contradiction_level = "minor_inconsistencies"

        # Base score from contradiction level
        base_score = CONTRADICTION_SCORES.get(
            contradiction_level, CONTRADICTION_SCORES["major_contradictions"]
        )  # pylint: disable=line-too-long

        score = base_score

        # Adjustments
        if causal_chain_intact:
            score += CAUSAL_CHAIN_BONUS
        if logical_gaps:
            score += LOGICAL_GAPS_PENALTY

        # DEPTH TEST: Critical penalty for frameworks operating only at hidāya layer
        if depth_borrowed_only_hidaya:
            # Framework operates only at behavior layer, borrowing from unexplained layers
            score += DEPTH_BORROWED_PENALTY
        elif depth_foundational:
            # Framework explains the foundational layers
            score += DEPTH_FOUNDATIONAL_BONUS

        # Clamp
        score = max(0, min(100, score))

        result = GateResult.SURVIVE if score >= SURVIVE_THRESHOLD else GateResult.FAIL

        reasoning_parts = [
            f"Contradiction level: {contradiction_level} (base={base_score})",
            f"Causal chain intact: {causal_chain_intact} ({'+' if causal_chain_intact else ''}{CAUSAL_CHAIN_BONUS if causal_chain_intact else 0})",  # pylint: disable=line-too-long
            f"Logical gaps: {logical_gaps} ({LOGICAL_GAPS_PENALTY if logical_gaps else 0})",
        ]

        if depth_borrowed_only_hidaya:
            reasoning_parts.append(
                f"Depth test (only hidāya layer): BORROWED from unexplained layers ({DEPTH_BORROWED_PENALTY})"
            )
        elif depth_foundational:
            reasoning_parts.append(
                f"Depth test (khalq→ṣūra→taqdīr→hidāya): FOUNDATIONAL ({'+' if depth_foundational else ''}{DEPTH_FOUNDATIONAL_BONUS if depth_foundational else 0})"
            )

        reasoning_parts.append(f"Final score: {score}/100 → {result.value}")

        return GateScore(
            name=self.name,
            score=score,
            result=result,
            reasoning="; ".join(reasoning_parts),
        )
