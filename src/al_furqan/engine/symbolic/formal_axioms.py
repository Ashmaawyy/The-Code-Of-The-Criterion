"""
Al-Furqan Formal Axioms — Z3 Encoding

Encodes the 3 Core Axioms + 2 Proofs from the Al-Furqan framework
as Z3 first-order logic formulas for formal verification.

Axioms encoded:
  1. Design Axiom — Existence implies purpose
  2. Network Axiom — Every entity has causal connections
  3. Alignment Axiom — Systems must align with purpose to function

Proofs encoded:
  1. Transcendence Necessity — Contingent frameworks cannot self-ground
  2. Final Court Necessity — Unresolved moral debts require a final court
"""

from z3 import (
    BoolSort,
    Const,
    DeclareSort,
    ForAll,
    Function,
    Implies,
    And,
    Not,
    Solver,
    sat,
)

# ---------------------------------------------------------------------------
# Core Sorts
# ---------------------------------------------------------------------------

# Entity: anything that exists (actions, systems, ideas, beings)
Entity = DeclareSort("Entity")

# Framework: an evaluative/philosophical system being tested
Framework = DeclareSort("Framework")

# ---------------------------------------------------------------------------
# Axiom 1 — Design: Existence implies purpose
# "If something exists, it must have a purpose."
# Purposeless design is a logical contradiction.
# ---------------------------------------------------------------------------

Exists_fn = Function("Exists", Entity, BoolSort())
HasPurpose = Function("HasPurpose", Entity, BoolSort())

x = Const("x", Entity)

axiom_design = ForAll([x], Implies(Exists_fn(x), HasPurpose(x)))

# ---------------------------------------------------------------------------
# Axiom 2 — Network: Every existing entity has causal connections
# "Every action produces compounded systemic consequences."
# No entity exists in isolation.
# ---------------------------------------------------------------------------

HasCausalNetwork = Function("HasCausalNetwork", Entity, BoolSort())

axiom_network = ForAll([x], Implies(Exists_fn(x), HasCausalNetwork(x)))

# ---------------------------------------------------------------------------
# Axiom 3 — Alignment: Functionality requires alignment with purpose
# "Normal behavior and systems are those aligned with optimal human
# functioning. Deviations compromise systemic well-being."
# Aligned(x) ↔ Functional(x) for all existing entities.
# ---------------------------------------------------------------------------

Aligned = Function("Aligned", Entity, BoolSort())
Functional = Function("Functional", Entity, BoolSort())

# Note: Z3 doesn't have Iff directly; we encode as And(Implies(A,B), Implies(B,A))
axiom_alignment = ForAll(
    [x],
    Implies(
        Exists_fn(x),
        And(
            Implies(Aligned(x), Functional(x)),
            Implies(Functional(x), Aligned(x)),
        ),
    ),
)

# ---------------------------------------------------------------------------
# Proof 1 — Transcendence Necessity
# "If a framework is contingent, it cannot self-ground and must have
# a transcendent source."
# Contingent → ¬CanSelfGround ∧ HasTranscendentSource
# ---------------------------------------------------------------------------

f = Const("f", Framework)

IsContingent = Function("IsContingent", Framework, BoolSort())
CanSelfGround = Function("CanSelfGround", Framework, BoolSort())
HasTranscendentSource = Function("HasTranscendentSource", Framework, BoolSort())

proof_transcendence = ForAll(
    [f],
    Implies(
        IsContingent(f),
        And(Not(CanSelfGround(f)), HasTranscendentSource(f)),
    ),
)

# ---------------------------------------------------------------------------
# Proof 2 — Final Court Necessity
# "If a framework has moral debts and human justice is insufficient,
# then a final non-contingent court is required."
# (HasMoralDebts ∧ ¬HumanJusticeSufficient) → RequiresFinalCourt
# ---------------------------------------------------------------------------

HasMoralDebts = Function("HasMoralDebts", Framework, BoolSort())
HumanJusticeSufficient = Function("HumanJusticeSufficient", Framework, BoolSort())
RequiresFinalCourt = Function("RequiresFinalCourt", Framework, BoolSort())

proof_final_court = ForAll(
    [f],
    Implies(
        And(HasMoralDebts(f), Not(HumanJusticeSufficient(f))),
        RequiresFinalCourt(f),
    ),
)

# ---------------------------------------------------------------------------
# All Axioms Collection
# ---------------------------------------------------------------------------

ALL_AXIOMS = [
    axiom_design,
    axiom_network,
    axiom_alignment,
    proof_transcendence,
    proof_final_court,
]

# ---------------------------------------------------------------------------
# Gate-Related Predicates
# These map to the Tri-Axial Survival Gates in the framework.
# ---------------------------------------------------------------------------

# Gate 1 — Source-Integrity: Does the entity have a verified transcendent source?
HasVerifiedSource = Function("HasVerifiedSource", Entity, BoolSort())

# Gate 2 — Structural-Consistency: Is the entity internally consistent?
IsInternallyConsistent = Function("IsInternallyConsistent", Entity, BoolSort())

# Gate 3 — Mediation-Zeroing: Is the entity free from human mediation as foundation?
FreeFromHumanMediation = Function("FreeFromHumanMediation", Entity, BoolSort())

# Gate 4 — Origin-Aware: Does the entity acknowledge transcendence?
AcknowledgesTranscendence = Function("AcknowledgesTranscendence", Entity, BoolSort())

# Additional: Does the entity preserve natural/fitrah order?
PreservesNatural = Function("PreservesNatural", Entity, BoolSort())

# All gate predicates for convenience
GATE_PREDICATES = [
    HasVerifiedSource,
    IsInternallyConsistent,
    FreeFromHumanMediation,
    AcknowledgesTranscendence,
    PreservesNatural,
]


def load_all_axioms():
    """Return a fresh copy of all axioms for use in a solver."""
    return list(ALL_AXIOMS)


def check_axioms_satisfiable() -> bool:
    """Quick sanity check: are the axioms themselves satisfiable?"""
    s = Solver()
    for ax in ALL_AXIOMS:
        s.add(ax)
    return s.check() == sat
