"""Tests for Z3 formal axiom encoding."""
# pylint: disable=duplicate-code

from z3 import Const, Not, Solver, sat, unsat

from al_furqan.engine.symbolic.formal_axioms import (
    ALL_AXIOMS,
    GATE_PREDICATES,
    Entity,
    Framework,
    Exists_fn,
    HasPurpose,
    HasCausalNetwork,
    Aligned,
    Functional,
    HasVerifiedSource,
    IsInternallyConsistent,
    AcknowledgesTranscendence,
    IsContingent,
    CanSelfGround,
    HasTranscendentSource,
    HasMoralDebts,
    HumanJusticeSufficient,
    RequiresFinalCourt,
    axiom_design,
    axiom_network,
    axiom_alignment,
    proof_transcendence,
    proof_final_court,
    load_all_axioms,
    check_axioms_satisfiable,
)


class TestAxiomSatisfiability:
    """Test that the axiom system is internally consistent."""

    def test_all_axioms_satisfiable(self):
        """Core axioms + proofs should be satisfiable together."""
        assert check_axioms_satisfiable() is True

    def test_axiom_count(self):
        """Should have exactly 5 axioms (3 core + 2 proofs)."""
        assert len(ALL_AXIOMS) == 5

    def test_gate_predicate_count(self):
        """Should have exactly 5 gate predicates."""
        assert len(GATE_PREDICATES) == 5

    def test_load_all_axioms_returns_copy(self):
        """load_all_axioms should return a new list each time."""
        a = load_all_axioms()
        b = load_all_axioms()
        assert a is not b
        assert len(a) == len(b) == 5


class TestDesignAxiom:
    """Axiom 1: Existence implies purpose."""

    def test_existing_entity_has_purpose(self):
        """If entity exists, it must have purpose — SAT."""
        s = Solver()
        s.add(axiom_design)
        e = Const("e1", Entity)
        s.add(Exists_fn(e))
        s.add(HasPurpose(e))
        assert s.check() == sat

    def test_existing_without_purpose_unsat(self):
        """An entity that exists but has no purpose contradicts design axiom."""
        s = Solver()
        s.add(axiom_design)
        e = Const("e1", Entity)
        s.add(Exists_fn(e))
        s.add(Not(HasPurpose(e)))
        assert s.check() == unsat


class TestNetworkAxiom:
    """Axiom 2: Every existing entity has causal connections."""

    def test_existing_entity_has_network(self):
        """Existing entity with causal network — SAT."""
        s = Solver()
        s.add(axiom_network)
        e = Const("e1", Entity)
        s.add(Exists_fn(e))
        s.add(HasCausalNetwork(e))
        assert s.check() == sat

    def test_existing_without_network_unsat(self):
        """Existing entity without causal network — UNSAT."""
        s = Solver()
        s.add(axiom_network)
        e = Const("e1", Entity)
        s.add(Exists_fn(e))
        s.add(Not(HasCausalNetwork(e)))
        assert s.check() == unsat


class TestAlignmentAxiom:
    """Axiom 3: Aligned ↔ Functional for existing entities."""

    def test_aligned_and_functional_sat(self):
        """Aligned and functional entity — SAT."""
        s = Solver()
        s.add(axiom_alignment)
        e = Const("e1", Entity)
        s.add(Exists_fn(e))
        s.add(Aligned(e))
        s.add(Functional(e))
        assert s.check() == sat

    def test_aligned_but_not_functional_unsat(self):
        """Aligned but not functional — contradicts biconditional — UNSAT."""
        s = Solver()
        s.add(axiom_alignment)
        e = Const("e1", Entity)
        s.add(Exists_fn(e))
        s.add(Aligned(e))
        s.add(Not(Functional(e)))
        assert s.check() == unsat

    def test_functional_but_not_aligned_unsat(self):
        """Functional but not aligned — contradicts biconditional — UNSAT."""
        s = Solver()
        s.add(axiom_alignment)
        e = Const("e1", Entity)
        s.add(Exists_fn(e))
        s.add(Functional(e))
        s.add(Not(Aligned(e)))
        assert s.check() == unsat


class TestTranscendenceProof:
    """Proof 1: Contingent frameworks cannot self-ground."""

    def test_contingent_has_transcendent_source(self):
        """Contingent + has transcendent source + cannot self-ground — SAT."""
        s = Solver()
        s.add(proof_transcendence)
        fw = Const("fw1", Framework)
        s.add(IsContingent(fw))
        s.add(Not(CanSelfGround(fw)))
        s.add(HasTranscendentSource(fw))
        assert s.check() == sat

    def test_contingent_claims_self_ground_unsat(self):
        """Contingent framework claiming it can self-ground — UNSAT."""
        s = Solver()
        s.add(proof_transcendence)
        fw = Const("fw1", Framework)
        s.add(IsContingent(fw))
        s.add(CanSelfGround(fw))
        assert s.check() == unsat

    def test_contingent_denies_transcendent_source_unsat(self):
        """Contingent framework denying transcendent source — UNSAT."""
        s = Solver()
        s.add(proof_transcendence)
        fw = Const("fw1", Framework)
        s.add(IsContingent(fw))
        s.add(Not(HasTranscendentSource(fw)))
        assert s.check() == unsat


class TestFinalCourtProof:
    """Proof 2: Unresolved moral debts require a final court."""

    def test_moral_debts_no_justice_requires_court(self):
        """Moral debts + no human justice + requires final court — SAT."""
        s = Solver()
        s.add(proof_final_court)
        fw = Const("fw1", Framework)
        s.add(HasMoralDebts(fw))
        s.add(Not(HumanJusticeSufficient(fw)))
        s.add(RequiresFinalCourt(fw))
        assert s.check() == sat

    def test_moral_debts_no_justice_no_court_unsat(self):
        """Moral debts + no human justice but denies final court — UNSAT."""
        s = Solver()
        s.add(proof_final_court)
        fw = Const("fw1", Framework)
        s.add(HasMoralDebts(fw))
        s.add(Not(HumanJusticeSufficient(fw)))
        s.add(Not(RequiresFinalCourt(fw)))
        assert s.check() == unsat

    def test_no_moral_debts_is_sat(self):
        """Framework without moral debts — axiom doesn't constrain — SAT."""
        s = Solver()
        s.add(proof_final_court)
        fw = Const("fw1", Framework)
        s.add(Not(HasMoralDebts(fw)))
        assert s.check() == sat


class TestCombinedScenarios:
    """Integration tests with all axioms together."""

    def test_divine_source_consistent_transcendent_sat(self):
        """System with divine source + consistent + acknowledges transcendence — SAT."""
        s = Solver()
        for ax in ALL_AXIOMS:
            s.add(ax)
        e = Const("system", Entity)
        s.add(Exists_fn(e))
        s.add(HasVerifiedSource(e))
        s.add(IsInternallyConsistent(e))
        s.add(AcknowledgesTranscendence(e))
        s.add(HasPurpose(e))
        s.add(HasCausalNetwork(e))
        s.add(Aligned(e))
        s.add(Functional(e))
        assert s.check() == sat

    def test_full_contradiction_unsat(self):
        """Entity exists but has no purpose and no network — UNSAT."""
        s = Solver()
        for ax in ALL_AXIOMS:
            s.add(ax)
        e = Const("broken", Entity)
        s.add(Exists_fn(e))
        s.add(Not(HasPurpose(e)))
        assert s.check() == unsat
