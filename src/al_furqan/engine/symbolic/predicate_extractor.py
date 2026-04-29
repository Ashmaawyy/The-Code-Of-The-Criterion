"""
Predicate Extractor — Maps chain/gate results to Z3 predicates.

Translates structured evaluation results (dicts from gate evaluations)
into Z3 boolean assertions that can be fed into the SymbolicVerifier.
"""

from z3 import Const, Not

from al_furqan.engine.symbolic.formal_axioms import (
    Entity,
    Framework,
    Exists_fn,
    HasPurpose,
    HasCausalNetwork,
    Aligned,
    Functional,
    HasVerifiedSource,
    IsInternallyConsistent,
    FreeFromHumanMediation,
    AcknowledgesTranscendence,
    PreservesNatural,
    IsContingent,
    CanSelfGround,
    HasTranscendentSource,
    HasMoralDebts,
    HumanJusticeSufficient,
    RequiresFinalCourt,
)


class PredicateExtractor:  # pylint: disable=too-few-public-methods
    """Extracts Z3-compatible predicates from chain/gate results.

    Maps structured evaluation data (from gate evaluation or verdict)
    into a list of Z3 assertions suitable for the SymbolicVerifier.

    Mapping rules:
        source_type == "divine" or is_verifiable == True  → HasVerifiedSource(e)
        has_contradictions == False                       → IsInternallyConsistent(e)
        relies_on_human_preference == False               → FreeFromHumanMediation(e)
        acknowledges_transcendence == True                → AcknowledgesTranscendence(e)
        preserves_natural == True                         → PreservesNatural(e)
        is_contingent == True                             → IsContingent(fw)
        can_self_ground == True/False                     → CanSelfGround(fw)
        has_transcendent_source == True/False              → HasTranscendentSource(fw)
        has_moral_debts == True                           → HasMoralDebts(fw)
        human_justice_sufficient == True/False            → HumanJusticeSufficient(fw)
        requires_final_court == True/False                → RequiresFinalCourt(fw)
        exists == True/False                              → Exists_fn(e)
        has_purpose == True/False                         → HasPurpose(e)
        aligned == True/False                             → Aligned(e)
        functional == True/False                          → Functional(e)
    """

    # Map from chain_results key → (Z3 function, sort, invert_logic)
    _ENTITY_MAPPINGS = {
        "has_contradictions": (
            IsInternallyConsistent,
            True,
        ),  # invert: no contradictions → consistent  # pylint: disable=line-too-long
        "relies_on_human_preference": (FreeFromHumanMediation, True),  # invert
        "acknowledges_transcendence": (AcknowledgesTranscendence, False),
        "preserves_natural": (PreservesNatural, False),
        "exists": (Exists_fn, False),
        "has_purpose": (HasPurpose, False),
        "aligned": (Aligned, False),
        "functional": (Functional, False),
        "has_causal_network": (HasCausalNetwork, False),
    }

    _FRAMEWORK_MAPPINGS = {
        "is_contingent": (IsContingent, False),
        "can_self_ground": (CanSelfGround, False),
        "has_transcendent_source": (HasTranscendentSource, False),
        "has_moral_debts": (HasMoralDebts, False),
        "human_justice_sufficient": (HumanJusticeSufficient, False),
        "requires_final_court": (RequiresFinalCourt, False),
    }

    def extract(self, chain_results: dict, entity_name: str = "subject") -> list:
        """Extract Z3 predicates from chain/gate results.

        Args:
            chain_results: Dictionary of evaluation results.
            entity_name: Name for the Z3 entity constant.

        Returns:
            List of Z3 boolean assertions.
        """
        if not chain_results:
            return []

        predicates = []
        entity = Const(entity_name, Entity)
        framework = Const(f"{entity_name}_framework", Framework)

        # Handle source verification (composite rule)
        self._extract_source_predicates(chain_results, entity, predicates)

        # Handle entity-level mappings
        for key, (z3_fn, invert) in self._ENTITY_MAPPINGS.items():
            if key in chain_results:
                value = chain_results[key]
                if not isinstance(value, bool):
                    continue
                if invert:
                    value = not value
                pred = z3_fn(entity) if value else Not(z3_fn(entity))
                predicates.append(pred)

        # Handle framework-level mappings
        for key, (z3_fn, invert) in self._FRAMEWORK_MAPPINGS.items():
            if key in chain_results:
                value = chain_results[key]
                if not isinstance(value, bool):
                    continue
                if invert:
                    value = not value
                pred = z3_fn(framework) if value else Not(z3_fn(framework))
                predicates.append(pred)

        return predicates

    def _extract_source_predicates(self, chain_results: dict, entity, predicates: list):
        """Handle the composite source verification logic.

        source_type == "divine" → HasVerifiedSource = True
        is_verifiable == True → HasVerifiedSource = True
        Both False/absent → HasVerifiedSource = False
        """
        has_verified = None

        if chain_results.get("source_type") == "divine":
            has_verified = True
        elif "is_verifiable" in chain_results:
            has_verified = chain_results["is_verifiable"]

        if has_verified is not None:
            if has_verified:
                predicates.append(HasVerifiedSource(entity))
            else:
                predicates.append(Not(HasVerifiedSource(entity)))
