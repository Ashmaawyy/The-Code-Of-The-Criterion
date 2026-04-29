"""
Symbolic Verifier — Z3 SMT-based formal verification.

Checks whether a set of predicates (extracted from gate/chain results)
is consistent with the Al-Furqan axiom system.

Results:
  - SAT (consistent=True): The predicates are compatible with the axioms.
  - UNSAT (consistent=False): The predicates contradict the axioms.
  - UNKNOWN (consistent=None): Solver timed out or was inconclusive.
"""

import time
from dataclasses import dataclass, field
from typing import Optional

from z3 import Solver, sat, unsat

from z3 import Const

from al_furqan.engine.symbolic.formal_axioms import (
    load_all_axioms,
    Entity,
    Framework,
    Exists_fn,
    HasPurpose,
    HasVerifiedSource,
    IsInternallyConsistent,
    FreeFromHumanMediation,
    AcknowledgesTranscendence,
    Aligned,
    Functional,
    IsContingent,
    HasTranscendentSource,
)
from al_furqan.engine.symbolic.predicate_extractor import PredicateExtractor


@dataclass
class VerificationResult:
    """Result of a Z3 verification check."""

    consistent: Optional[bool]  # True=sat, False=unsat, None=unknown
    proof: str  # Human-readable proof/disproof explanation
    contradictions: list = field(default_factory=list)  # Details when unsat
    verification_time_ms: float = 0.0


class SymbolicVerifier:
    """Formal verification using Z3 SMT solver.

    Loads the Al-Furqan axiom system and checks whether additional
    predicates (from gate evaluations) are consistent with it.
    """

    def __init__(self, timeout_ms: int = 10000):
        """Initialize with timeout for Z3 solver.

        Args:
            timeout_ms: Maximum time in milliseconds for the solver.
        """
        self.timeout_ms = timeout_ms
        self.axioms = load_all_axioms()
        self._extractor = PredicateExtractor()

    def verify(self, predicates: list) -> VerificationResult:
        """Verify predicates against the axiom system.

        1. Create solver with core axioms
        2. Add extracted predicates
        3. Check satisfiability
        4. Return result with proof/disproof

        Args:
            predicates: List of Z3 boolean assertions to check.

        Returns:
            VerificationResult with consistency status and explanation.
        """
        solver = Solver()
        solver.set("timeout", self.timeout_ms)

        # Add core axioms
        for axiom in self.axioms:
            solver.add(axiom)

        # Add predicates under test
        for pred in predicates:
            solver.add(pred)

        # Check satisfiability
        start = time.monotonic()
        try:
            result = solver.check()
        except Exception as e:  # pylint: disable=broad-exception-caught
            elapsed = (time.monotonic() - start) * 1000
            return VerificationResult(
                consistent=None,
                proof=f"Solver error: {e}",
                verification_time_ms=elapsed,
            )
        elapsed = (time.monotonic() - start) * 1000

        if result == sat:  # pylint: disable=no-else-return
            return VerificationResult(
                consistent=True,
                proof="The predicates are consistent with all Al-Furqan axioms. "
                "A satisfying model exists.",
                verification_time_ms=elapsed,
            )
        elif result == unsat:
            # Try to extract unsat core for diagnostics
            contradictions = self._extract_contradictions(predicates)
            return VerificationResult(
                consistent=False,
                proof="The predicates contradict the Al-Furqan axiom system. "
                "No satisfying model exists.",
                contradictions=contradictions,
                verification_time_ms=elapsed,
            )
        else:
            return VerificationResult(
                consistent=None,
                proof="The solver was unable to determine satisfiability "
                "(timeout or resource limit reached).",
                verification_time_ms=elapsed,
            )

    def _extract_contradictions(self, predicates: list) -> list:
        """Attempt to identify which predicates cause the contradiction.

        Uses incremental solving to find a minimal conflicting subset.
        """
        contradictions = []
        solver = Solver()
        solver.set("timeout", self.timeout_ms)

        for axiom in self.axioms:
            solver.add(axiom)

        # Add predicates one by one to find the breaking point
        added = []
        for pred in predicates:
            solver.add(pred)
            added.append(pred)
            if solver.check() == unsat:
                contradictions.append(f"Contradiction introduced by predicate: {pred}")
                break

        return contradictions

    def verify_gate_consistency(self, gate_results: dict) -> VerificationResult:
        """Verify that gate evaluation results are consistent with axioms.

        Extracts predicates from gate results and verifies them.

        Args:
            gate_results: Dictionary of gate evaluation outcomes.

        Returns:
            VerificationResult with consistency status.
        """
        predicates = self._extractor.extract(gate_results)
        return self.verify(predicates)

    def verify_verdict(self, verdict_data: dict) -> VerificationResult:
        """Full verdict verification: extract predicates + verify.

        Handles the complete pipeline from raw verdict data to
        formal verification result.

        Args:
            verdict_data: Dictionary containing verdict/evaluation data.
                Expected keys match PredicateExtractor mappings.

        Returns:
            VerificationResult with full verification details.
        """
        entity_name = verdict_data.get("entity_name", "subject")
        predicates = self._extractor.extract(verdict_data, entity_name=entity_name)
        return self.verify(predicates)

    def verify_per_gate(self, verdict_data: dict) -> dict[str, VerificationResult]:  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        """Verify each gate independently against axioms.

        Instead of one holistic check, runs 4 separate verifications —
        one per gate — each with only the predicates relevant to that gate.

        Returns:
            Dict mapping gate name → VerificationResult.
            Example: {"source_integrity": SAT, "structural_consistency": UNSAT, ...}
        """
        from z3 import Not as Z3Not  # pylint: disable=import-outside-toplevel

        entity_name = verdict_data.get("entity_name", "subject")
        entity = Const(entity_name, Entity)
        framework = Const(f"{entity_name}_framework", Framework)

        results = {}

        # ── Gate 1: Source Integrity ──
        # A valid source must be verified. If source is human_theory
        # and claims to be self-grounding → contradiction.
        g1_predicates = []
        source_type = verdict_data.get("source_type", "")
        is_verifiable = verdict_data.get("is_verifiable", False)
        contradicts = verdict_data.get("contradicts_primary", False)

        if source_type == "divine" and is_verifiable:
            g1_predicates.append(HasVerifiedSource(entity))
        elif source_type == "human_theory":
            g1_predicates.append(Z3Not(HasVerifiedSource(entity)))
            g1_predicates.append(IsContingent(framework))
            # Human theory is contingent → must have transcendent source (axiom)
            # but it doesn't → contradiction
            if not verdict_data.get("has_transcendent_source", False):
                g1_predicates.append(Z3Not(HasTranscendentSource(framework)))
        elif not is_verifiable:
            g1_predicates.append(Z3Not(HasVerifiedSource(entity)))

        if contradicts:
            g1_predicates.append(Z3Not(IsInternallyConsistent(entity)))

        results["source_integrity"] = (
            self.verify(g1_predicates)
            if g1_predicates
            else VerificationResult(  # pylint: disable=line-too-long
                consistent=True, proof="No predicates to verify for this gate."
            )
        )

        # ── Gate 2: Structural Consistency ──
        # Internal contradictions violate the Alignment axiom:
        # if not aligned → not functional.
        g2_predicates = []
        has_contradictions = verdict_data.get(
            "has_contradictions", verdict_data.get("contradicts_primary", False)
        )
        has_logical_gaps = verdict_data.get("has_logical_gaps", False)
        consistency = verdict_data.get("consistency_level", "")

        g2_predicates.append(Exists_fn(entity))
        g2_predicates.append(HasPurpose(entity))

        if has_contradictions or consistency == "major_contradictions":
            # Contradictions → not aligned → not functional (by axiom 3)
            g2_predicates.append(Z3Not(Aligned(entity)))
            # But claim it's functional → contradiction
            if not has_logical_gaps:
                g2_predicates.append(Functional(entity))
            else:
                g2_predicates.append(Z3Not(Functional(entity)))
        elif consistency == "no_contradictions" and not has_logical_gaps:
            g2_predicates.append(Aligned(entity))
            g2_predicates.append(Functional(entity))

        results["structural_consistency"] = self.verify(g2_predicates)

        # ── Gate 3: Mediation Zeroing ──
        # Pure human preference as foundation = contingent system
        # trying to ground itself → violates Transcendence Necessity.
        g3_predicates = []
        foundation = verdict_data.get("foundation_type", "")
        relies_human = verdict_data.get(
            "relies_on_human_preference", foundation == "pure_human_preference"
        )

        if relies_human or foundation == "pure_human_preference":
            g3_predicates.append(Z3Not(FreeFromHumanMediation(entity)))
            g3_predicates.append(IsContingent(framework))
            # Contingent but no transcendent source → violates axiom
            if not verdict_data.get("acknowledges_transcendence", False):
                g3_predicates.append(Z3Not(HasTranscendentSource(framework)))
        elif foundation == "non_human_foundation":
            g3_predicates.append(FreeFromHumanMediation(entity))

        results["mediation_zeroing"] = (
            self.verify(g3_predicates)
            if g3_predicates
            else VerificationResult(  # pylint: disable=line-too-long
                consistent=True, proof="No predicates to verify for this gate."
            )
        )

        # ── Gate 4: Origin Aware ──
        # Denying transcendence while being contingent → direct axiom violation.
        g4_predicates = []
        ack_transcendence = verdict_data.get("acknowledges_transcendence", False)

        g4_predicates.append(Exists_fn(entity))
        g4_predicates.append(HasPurpose(entity))

        if not ack_transcendence:
            g4_predicates.append(Z3Not(AcknowledgesTranscendence(entity)))
            # If contingent and denies transcendent source
            is_contingent = verdict_data.get(
                "is_contingent", verdict_data.get("source_type", "") == "human_theory"
            )
            if is_contingent:
                g4_predicates.append(IsContingent(framework))
                g4_predicates.append(Z3Not(HasTranscendentSource(framework)))
        else:
            g4_predicates.append(AcknowledgesTranscendence(entity))
            if verdict_data.get("has_transcendent_source", True):
                g4_predicates.append(HasTranscendentSource(framework))

        results["origin_aware"] = self.verify(g4_predicates)

        return results
