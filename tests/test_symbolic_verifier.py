"""Tests for the SymbolicVerifier."""

from z3 import Const, Not

from al_furqan.engine.symbolic.verifier import SymbolicVerifier, VerificationResult
from al_furqan.engine.symbolic.formal_axioms import (
    Entity,
    Framework,
    Exists_fn,
    HasPurpose,
    HasCausalNetwork,
    Aligned,
    Functional,
    IsContingent,
    CanSelfGround,
    HasMoralDebts,
    HumanJusticeSufficient,
    RequiresFinalCourt,
)


class TestSymbolicVerifier:
    """Test the full verification pipeline."""

    def setup_method(self):
        """Execute setup_method."""
        # pylint: disable=attribute-defined-outside-init
        self.verifier = SymbolicVerifier(timeout_ms=5000)

    def test_empty_predicates_sat(self):
        """No additional predicates — axioms alone are SAT."""
        result = self.verifier.verify([])
        assert result.consistent is True
        assert result.verification_time_ms >= 0

    def test_consistent_entity_sat(self):
        """Fully consistent entity should be SAT."""
        e = Const("test_entity", Entity)
        predicates = [
            Exists_fn(e),
            HasPurpose(e),
            HasCausalNetwork(e),
            Aligned(e),
            Functional(e),
        ]
        result = self.verifier.verify(predicates)
        assert result.consistent is True

    def test_exists_without_purpose_unsat(self):
        """Entity exists but has no purpose — UNSAT."""
        e = Const("purposeless", Entity)
        predicates = [
            Exists_fn(e),
            Not(HasPurpose(e)),
        ]
        result = self.verifier.verify(predicates)
        assert result.consistent is False
        assert len(result.contradictions) > 0

    def test_contingent_self_grounding_unsat(self):
        """Contingent framework claiming self-grounding — UNSAT."""
        fw = Const("secular", Framework)
        predicates = [
            IsContingent(fw),
            CanSelfGround(fw),
        ]
        result = self.verifier.verify(predicates)
        assert result.consistent is False

    def test_moral_debts_no_court_unsat(self):
        """Moral debts + no human justice + no final court — UNSAT."""
        fw = Const("unjust", Framework)
        predicates = [
            HasMoralDebts(fw),
            Not(HumanJusticeSufficient(fw)),
            Not(RequiresFinalCourt(fw)),
        ]
        result = self.verifier.verify(predicates)
        assert result.consistent is False

    def test_aligned_not_functional_unsat(self):
        """Aligned but not functional — violates biconditional — UNSAT."""
        e = Const("misaligned", Entity)
        predicates = [
            Exists_fn(e),
            Aligned(e),
            Not(Functional(e)),
        ]
        result = self.verifier.verify(predicates)
        assert result.consistent is False

    def test_verification_result_fields(self):
        """VerificationResult should have all expected fields."""
        result = self.verifier.verify([])
        assert isinstance(result, VerificationResult)
        assert isinstance(result.consistent, bool)
        assert isinstance(result.proof, str)
        assert isinstance(result.contradictions, list)
        assert isinstance(result.verification_time_ms, float)

    def test_timeout_returns_unknown(self):
        """Very short timeout should return unknown (or sat for simple cases)."""
        # With a 1ms timeout, complex queries might time out
        fast_verifier = SymbolicVerifier(timeout_ms=1)
        result = fast_verifier.verify([])
        # For simple cases even 1ms is enough, so we accept sat or unknown
        assert result.consistent in (True, None)


class TestVerifyGateConsistency:
    """Test gate consistency verification."""

    def setup_method(self):
        """Execute setup_method."""
        # pylint: disable=attribute-defined-outside-init
        self.verifier = SymbolicVerifier(timeout_ms=5000)

    def test_divine_consistent_framework_sat(self):
        """Divine source + consistent + transcendent → SAT."""
        gate_results = {
            "source_type": "divine",
            "has_contradictions": False,
            "relies_on_human_preference": False,
            "acknowledges_transcendence": True,
        }
        result = self.verifier.verify_gate_consistency(gate_results)
        assert result.consistent is True

    def test_empty_gate_results_sat(self):
        """Empty gate results — just axioms — SAT."""
        result = self.verifier.verify_gate_consistency({})
        assert result.consistent is True


class TestVerifyVerdict:
    """Test full verdict verification."""

    def setup_method(self):
        """Execute setup_method."""
        # pylint: disable=attribute-defined-outside-init
        self.verifier = SymbolicVerifier(timeout_ms=5000)

    def test_full_verdict_sat(self):
        """Complete consistent verdict — SAT."""
        verdict = {
            "entity_name": "quran",
            "source_type": "divine",
            "has_contradictions": False,
            "relies_on_human_preference": False,
            "acknowledges_transcendence": True,
            "exists": True,
            "has_purpose": True,
            "has_causal_network": True,
            "aligned": True,
            "functional": True,
        }
        result = self.verifier.verify_verdict(verdict)
        assert result.consistent is True

    def test_contradictory_verdict_unsat(self):
        """Verdict with exists=True but has_purpose=False — UNSAT."""
        verdict = {
            "exists": True,
            "has_purpose": False,
        }
        result = self.verifier.verify_verdict(verdict)
        assert result.consistent is False

    def test_framework_verdict_with_transcendence_denial(self):
        """Contingent framework denying transcendence — UNSAT."""
        verdict = {
            "is_contingent": True,
            "has_transcendent_source": False,
        }
        result = self.verifier.verify_verdict(verdict)
        assert result.consistent is False

    def test_framework_verdict_with_proper_transcendence(self):
        """Contingent framework accepting transcendence — SAT."""
        verdict = {
            "is_contingent": True,
            "can_self_ground": False,
            "has_transcendent_source": True,
        }
        result = self.verifier.verify_verdict(verdict)
        assert result.consistent is True
