# Visual Architecture: The Criterion as LLM Reasoning Framework

## The Complete Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER QUERY / PROPOSAL                              │
└────────────────────────────────────┬────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LLM SEMANTIC UNDERSTANDING LAYER                         │
│                                                                              │
│  Question: What domain? What assumptions? What's the true intent?          │
│                                                                              │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┬──────────────┐  │
│  │  Economic   │   Social    │  Spiritual  │Intellectual │  Biological  │  │
│  │   Domain    │   Domain    │   Domain    │   Domain    │   Domain     │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┴──────────────┘  │
│                                                                              │
│  Output: system_data = {                                                   │
│    "permits_exploitative_gain": ?,                                         │
│    "acknowledges_transcendent_source": ?,                                  │
│    "enables_accountability": ?,                                            │
│    "causes_harm_amplification": ?,                                         │
│    "deviates_from_optimal_functioning": ?,                                 │
│    "destabilizes_lineage": ?                                               │
│  }                                                                          │
└────────────────────────────────────┬────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CRITERION REASONING ENGINE LAYER                         │
│                     (CriterionReasoningEngine.reason())                     │
│                                                                              │
│  ╔════════════════════════════════════════════════════════════════════╗    │
│  ║ PHASE 1: SCAN                                                      ║    │
│  ║ Identify primary domain and secondary contexts                     ║    │
│  ╚═══════════════════════════╦═══════════════════════════════════════╝    │
│                              ▼                                              │
│  ╔════════════════════════════════════════════════════════════════════╗    │
│  ║ PHASE 2: EXTRACT                                                  ║    │
│  ║ Parse embedded assumptions and inferred intent                    ║    │
│  ╚═══════════════════════════╦═══════════════════════════════════════╝    │
│                              ▼                                              │
│  ╔════════════════════════════════════════════════════════════════════╗    │
│  ║ PHASE 3: MIRROR                                                   ║    │
│  ║ Check axiom compliance and identify "frictions"                  ║    │
│  ║                                                                  ║    │
│  ║ ┌─────────────────────┐  ┌──────────────────────┐              ║    │
│  ║ │ 5 Foundational      │  │ Axiom Compliance     │              ║    │
│  ║ │ Axioms              │  │                      │              ║    │
│  ║ │                     │  │ ✓ or ✗ for each:    │              ║    │
│  ║ │ 1. Transcendence    │  │ - Transcendence      │              ║    │
│  ║ │ 2. Final Court      │  │ - Accountability     │              ║    │
│  ║ │ 3. Design vs Accident│ │ - Design vs Accident │              ║    │
│  ║ │ 4. Definition Normal│  │ - Definition Normal  │              ║    │
│  ║ │ 5. Network Effect   │  │ - Network Effect     │              ║    │
│  ║ └─────────────────────┘  └──────────────────────┘              ║    │
│  ╚═══════════════════════════╦═══════════════════════════════════════╝    │
│                              ▼                                              │
│  ╔════════════════════════════════════════════════════════════════════╗    │
│  ║ PHASE 4: GATES                                                    ║    │
│  ║ Apply 4 tri-axial survival filters                               ║    │
│  ║                                                                  ║    │
│  ║ ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐║    │
│  ║ │ Source Integrity │  │ Structural       │  │ Mediation       ││    │
│  ║ │ 0-100 score      │  │ Consistency      │  │ Zeroing         ││    │
│  ║ │ Pass if > 0      │  │ 0-100 score      │  │ 0-100 score     ││    │
│  ║ └──────────────────┘  │ Pass if > 0      │  │ Pass if > 0     ││    │
│  ║                       └──────────────────┘  └─────────────────┘║    │
│  ║                                                                  ║    │
│  ║ ┌─────────────────────────────────────────────────────────────┐ ║    │
│  ║ │ Origin Aware (MANDATORY)                                   │ ║    │
│  ║ │ Must = 100 or ENTIRE SYSTEM FAILS                         │ ║    │
│  ║ └─────────────────────────────────────────────────────────────┘ ║    │
│  ╚═══════════════════════════╦═══════════════════════════════════════╝    │
│                              ▼                                              │
│  ╔════════════════════════════════════════════════════════════════════╗    │
│  ║ PHASE 5: CONSEQUENCES                                             ║    │
│  ║ Trace cascading network effects across domains                   ║    │
│  ║                                                                  ║    │
│  ║ Harm Level                    Timeline        Reversibility      ║    │
│  ║ ├─ Localized                  ├─ Immediate    ├─ Reversible     ║    │
│  ║ ├─ Moderate                   ├─ 1-3 years    ├─ Hard to reverse║    │
│  ║ ├─ Significant                ├─ 2-10 years   └─ Irreversible   ║    │
│  ║ └─ Severe/Collapse            └─ Generational                   ║    │
│  ╚═══════════════════════════╦═══════════════════════════════════════╝    │
│                              ▼                                              │
│  ╔════════════════════════════════════════════════════════════════════╗    │
│  ║ PHASE 6: VERDICT                                                  ║    │
│  ║ Final judgment with full reasoning chain                          ║    │
│  ║                                                                  ║    │
│  ║ Decision: SURVIVES or FAILS The Criterion                        ║    │
│  ║ Reasoning: [Explicit axiom-based explanation]                    ║    │
│  ║ Recommendation: [ACCEPT/CONDITIONAL/REJECT]                      ║    │
│  ║ Critical Issues: [List of axiom violations]                      ║    │
│  ╚════════════════════════════════════════════════════════════════════╝    │
│                                                                              │
└────────────────────────────────────┬────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CHAIN-OF-THOUGHT SCAFFOLD OUTPUT                        │
│                                                                              │
│  THINKING STRUCTURE FOR LLM (not free generation)                          │
│                                                                              │
│  PHASE 1 - SCAN: [domain] domain identified                               │
│  → Therefore, [domain]-specific axioms apply                              │
│                                                                              │
│  PHASE 2 - EXTRACT: [N] assumptions, intent = [X]                         │
│  → Therefore, proposal attempts [Y]                                        │
│                                                                              │
│  PHASE 3 - MIRROR: [N] violations (critical/high/medium/low)              │
│  → Therefore, system has [N] design flaws                                 │
│                                                                              │
│  PHASE 4 - GATES:                                                          │
│  - Source Integrity: [score]/100                                           │
│  - Structural Consistency: [score]/100                                     │
│  - Mediation Zeroing: [score]/100                                          │
│  - Origin Aware: [score]/100 [CRITICAL]                                    │
│  → Therefore, system [PASSES/FAILS] gates                                  │
│                                                                              │
│  PHASE 5 - CONSEQUENCES: [N] affected domains                              │
│  → Therefore, harm compounds across all systems                            │
│                                                                              │
│  PHASE 6 - VERDICT: [SURVIVES/FAILS]                                       │
│  Recommendation: [ACCEPT/CONDITIONAL/REJECT]                               │
│                                                                              │
└────────────────────────────────────┬────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LLM GENERATION LAYER                               │
│                                                                              │
│  Instead of:  "Well, here are some arguments for both sides..."           │
│                                                                              │
│  Now:          "Based on Criterion analysis:                              │
│                                                                              │
│                 [Follow CoT scaffold]                                       │
│                                                                              │
│                 PHASE 1: Economic domain...                                │
│                 PHASE 2: Assumptions reveal...                             │
│                 PHASE 3: Violates axiom of...                              │
│                 PHASE 4: All gates fail...                                 │
│                 PHASE 5: Harm cascades...                                  │
│                 PHASE 6: This FAILS The Criterion"                         │
│                                                                              │
│  Output: Guaranteed architecturally sound reasoning                        │
│          Every conclusion traceable to logic                               │
│          Not probabilistic, but principled                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AXIOM-ALIGNED OUTPUT                                 │
│                                                                              │
│  ✓ Traceable to specific axioms                                             │
│  ✓ Auditable reasoning chain                                               │
│  ✓ Deterministic (not probabilistic)                                       │
│  ✓ Cannot be tricked (logic cannot be fooled)                              │
│  ✓ Updatable (change axioms → change outputs)                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Decision Trees

### PHASE 3: Axiom Compliance Check
```
System analysis
    │
    ├─ TRANSCENDENCE NECESSITY
    │  └─ Acknowledges non-contingent source?
    │     ├─ YES → Pass
    │     └─ NO  → CRITICAL VIOLATION
    │
    ├─ FINAL COURT NECESSITY
    │  └─ Enables ultimate accountability?
    │     ├─ YES → Pass
    │     └─ NO  → CRITICAL VIOLATION
    │
    ├─ DESIGN VS ACCIDENT
    │  └─ Is system designed/intentional?
    │     ├─ YES → Pass
    │     └─ NO  → HIGH VIOLATION
    │
    ├─ DEFINITION OF NORMAL
    │  └─ Enables optimal functioning?
    │     ├─ YES → Pass
    │     └─ NO  → HIGH VIOLATION
    │
    └─ NETWORK EFFECT
       └─ Do benefits compound to global harm?
          ├─ NO  → Pass
          └─ YES → CRITICAL VIOLATION
```

### PHASE 4: Gate Evaluation
```
All 4 Gates Pass?
    │
    ├─ NO → Check Origin Aware = 100?
    │  ├─ NO  → FAIL (cannot pass with 0 score)
    │  └─ YES → Check other gates > 0?
    │     ├─ NO  → FAIL (gate failure)
    │     └─ YES → Continue to Phase 5
    │
    └─ YES → Continue to consequences
             (all gates score > 0, Origin = 100)
```

### OVERALL: SURVIVES vs FAILS
```
System Analysis
    │
    ├─ Does Origin Aware gate = 100?
    │  │
    │  ├─ NO  → FAILS (mandatory gate failed)
    │  │
    │  └─ YES → Do all other gates score > 0?
    │     │
    │     ├─ NO  → FAILS (gate failure)
    │     │
    │     └─ YES → Any critical axiom violations?
    │        │
    │        ├─ 3+ violations → FAILS (critical)
    │        │
    │        ├─ 1-2 violations → CONDITIONAL (needs fixes)
    │        │
    │        └─ 0 violations → SURVIVES ✓
```

---

## Gate Scoring Guide

```
Score 100/100          Score 0-90            Score 0
═══════════════════    ═══════════════════   ═══════════════════
✓ Excellent            ⚠ Concerning          ✗ FAILS
✓ Fully aligned        ⚠ Partial alignment   ✗ No alignment
✓ Passes gate          ⚠ Risky               ✗ Automatic fail

Example:               Example:               Example:
Origin Aware = 100     Source Integrity = 45 Transcendence = 0
(YES to transcendence)(Partial truth,        (NO transcendent
                      some distortion)       source at all)
```

---

## Verdict Classification

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           VERDICT MATRIX                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ Origin Aware    Gates Pass?    Axiom              Verdict               │
│ = 100?          (all > 0)      Violations                               │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ NO              —              —                  FAILS (Gate 0)        │
│                                                   ✗ Complete reject     │
│                                                                          │
│ YES             NO             —                  FAILS (Gate 0)        │
│                                                   ✗ Complete reject     │
│                                                                          │
│ YES             YES            3+ violations      FAILS (Critical)      │
│                                                   ✗ Redesign required   │
│                                                                          │
│ YES             YES            1-2 violations     CONDITIONAL           │
│                                                   ⚠ Fix issues & retry  │
│                                                                          │
│ YES             YES            0 violations       SURVIVES ✓            │
│                                                   ✓ Accept as-is        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: LLM to Output

```
INPUT: User Query
    │
    ├─ [LLM Semantic Layer]
    │  └─ Extracts: domain, assumptions, intent
    │     └─ Returns: system_data dict
    │
    ├─ [CriterionPipeline.evaluate()]
    │  └─ Runs: 6-phase reasoning
    │     └─ Returns: structured analysis
    │
    ├─ [CoT Scaffold Generation]
    │  └─ Formats: thinking structure
    │     └─ Returns: readable phases
    │
    └─ [LLM Generation]
       └─ Follows: scaffold (not free-text)
          └─ Output: Axiom-aligned reasoning
```

---

## Summary: How It Works

1. **LLM understands** what domain and what assumptions
2. **Reasoning Engine structures** the thinking in 6 phases
3. **Axioms judge** if the system design is sound
4. **Gates filter** if the system survives
5. **Consequences show** what damage it causes
6. **Verdict judges** SURVIVES or FAILS
7. **LLM generates** following the scaffold (not freely)
8. **Output is guaranteed** axiom-aligned

The result: Not intelligence that seems reasonable, but intelligence that IS reasonable.
