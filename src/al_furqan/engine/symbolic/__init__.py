# Symbolic reasoning — Sprint 4  # pylint: disable=missing-module-docstring

from al_furqan.engine.symbolic.formal_axioms import (
    ALL_AXIOMS,
    GATE_PREDICATES,
    AcknowledgesTranscendence,
    Aligned,
    CanSelfGround,
    Entity,
    Exists_fn,
    Framework,
    FreeFromHumanMediation,
    Functional,
    HasCausalNetwork,
    HasMoralDebts,
    HasPurpose,
    HasTranscendentSource,
    HasVerifiedSource,
    HumanJusticeSufficient,
    IsContingent,
    IsInternallyConsistent,
    PreservesNatural,
    RequiresFinalCourt,
    axiom_alignment,
    axiom_design,
    axiom_network,
    check_axioms_satisfiable,
    load_all_axioms,
    proof_final_court,
    proof_transcendence,
)
from al_furqan.engine.symbolic.predicate_extractor import PredicateExtractor
from al_furqan.engine.symbolic.verifier import SymbolicVerifier, VerificationResult

__all__ = [
    # Axioms
    "ALL_AXIOMS",
    "GATE_PREDICATES",
    "axiom_design",
    "axiom_network",
    "axiom_alignment",
    "proof_transcendence",
    "proof_final_court",
    "load_all_axioms",
    "check_axioms_satisfiable",
    # Sorts
    "Entity",
    "Framework",
    # Entity predicates
    "Exists_fn",
    "HasPurpose",
    "HasCausalNetwork",
    "Aligned",
    "Functional",
    # Gate predicates
    "HasVerifiedSource",
    "IsInternallyConsistent",
    "FreeFromHumanMediation",
    "AcknowledgesTranscendence",
    "PreservesNatural",
    # Framework predicates
    "IsContingent",
    "CanSelfGround",
    "HasTranscendentSource",
    "HasMoralDebts",
    "HumanJusticeSufficient",
    "RequiresFinalCourt",
    # Classes
    "PredicateExtractor",
    "SymbolicVerifier",
    "VerificationResult",
]
