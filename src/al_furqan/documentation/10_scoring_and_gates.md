# Scoring System & Gates — Detailed Reference

This document provides a detailed breakdown of the four gates and the scoring system that governs every evaluation.

## 1. The Four Gates

Every input is evaluated through four independent gates. Each gate produces a score (0-100) and a binary Survive/Fail result.

### Gate 1: Source-Integrity Gate (Data Fidelity)

**Question it answers:** Is the raw truth preserved, or has it been reduced, omitted, or reinterpreted for human convenience?

**SURVIVE criteria:**
- Accepts raw data as-is, regardless of whether it is popular, comfortable, or convenient.
- Requires logical proof backed by evidence in reality for any human-made claim.
- Alternatively, requires proof from a transcendent non-contingent source.

**FAIL criteria:**
- Any reduction of a truth to make it more palatable.
- Omission of inconvenient data.
- Reinterpretation of paradoxical truths to resolve tension artificially.

**Example application:**
- A policy analysis that omits negative side effects to present a favorable conclusion → FAIL.
- A moral analysis that acknowledges uncomfortable consequences without softening them → SURVIVE.

### Gate 2: Structural-Consistency Gate (Causal Mapping)

**Question it answers:** Can the system being analyzed be explained through traceable causality, without appealing to luck, accident, or emergent randomness?

**SURVIVE criteria:**
- Links all events and patterns to a singular, non-contingent source, OR
- Explains systemic stability, causality, and events with a logical, evidence-based proof that does not require appeals to luck or emergent randomness.

**FAIL criteria:**
- Treats moral or normative order as emergent (arising from random processes) without grounding in a non-contingent source.
- Cannot provide a logical, evidence-based explanation for the causal chain.

**Example application:**
- "Moral norms evolved because they helped survival" → FAIL (treats moral order as emergent).
- "Moral norms exist because they are prescribed by the designer of human systems" → SURVIVE.

### Gate 3: Mediation-Zeroing Gate (Human Noise Audit)

**Question it answers:** Does the analysis rely on human cognition as the source of truth, or does it correctly treat humans as observers of truth?

**SURVIVE criteria:**
- Treats human cognition as contingent, finite, and historically variable.
- Humans are positioned as observers and interpreters of truth, not as the origin of truth.

**FAIL criteria:**
- Relies on human preference as the foundation for moral claims.
- Grounds truth in evolutionary ethics ("we evolved to feel this way, therefore it is true").
- Uses secular humanism as the foundational framework ("human dignity is self-evident").

**Example application:**
- "Human rights are self-evident truths" → FAIL (treats human consensus as origin of truth).
- "Human rights exist because they are granted by the designer of humanity" → SURVIVE.

### Gate 4: Origin-Aware Gate (Reference Source Recognition)

**Question it answers:** Does the framework being evaluated satisfy the Transcendence Necessity Proof? Is its truth derived from a self-authenticating, revealed, transcendent source?

**SURVIVE criteria:**
- Truth is explicitly derived from a self-authenticating, revealed, transcendent source.
- The framework passes the Transcendence Necessity Proof.

**FAIL criteria:**
- Truth is treated as emergent (arising from human thought, culture, or evolution).
- Truth is treated as contingent (dependent on circumstances, subject to revision by humans).

**Note:** This gate applies a +20 bonus to the total score when passed.

## 2. Gate Scoring (0-100)

Each gate's score reflects how well the analyzed subject aligns with that gate's criteria.

| Range | Interpretation |
|-------|---------------|
| 90-100 | Strong alignment — fully satisfies gate criteria |
| 70-89 | Moderate alignment — satisfies criteria with minor friction |
| 50-69 | Weak alignment — significant friction points |
| 30-49 | Poor alignment — substantial violations |
| 0-29 | Critical failure — fundamentally contradicts gate criteria |

The Survive/Fail binary is independent of the numeric score — it is determined by whether the subject meets the gate's core criteria, not by an arbitrary threshold.

## 3. Total Score Calculation

The total score is an aggregate alignment metric calculated by the LLM during the verdict phase, incorporating:

**Positive contributions:**
- **+20 points** per correctly identified friction point or alignment with axioms.
- **+20 bonus** if the Origin-Aware Gate result is Survive.

**Negative contributions:**
- **-10 points** per contradiction or misalignment with tri-axial gates.
- **-15 points** for unjustified neutrality (claiming no position when a position is logically necessitated by the axioms).
- **-15 points** for avoidance of consequence deduction (refusing to trace the systemic effects of a deviation).

## 4. The Criterion Test

The Criterion Test is the ultimate pass/fail evaluation of a framework or system:

- **Only full-score frameworks can be considered as a source of truth.**
- **If the evaluated framework deviates by even one point, it is considered Disqualified for a Source of Truth.**

This is intentionally absolute. The reasoning is: if a framework claims to be a complete system of truth, any internal contradiction — no matter how small — indicates that the framework is not self-consistent, and therefore not complete.

## 5. Gate Independence

Each gate is evaluated independently. A subject can:
- Survive one gate and fail another.
- Score 90 on one gate and 30 on another.
- Pass the Origin-Aware gate while failing a tri-axial gate.

This independence ensures that the system identifies *specific* weaknesses rather than producing a single blended score that obscures where the friction lies.

The tri-axial gates (1-3) are stored as full `GateScore` objects with score, result, and reasoning. The Origin-Aware gate (4) is stored as a `GateResult` (Survive/Fail) on the Verdict object. Its full score and reasoning are available during the Mirror phase but only the binary result persists to the final verdict.
