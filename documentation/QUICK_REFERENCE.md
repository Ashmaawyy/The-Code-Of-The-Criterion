# Quick Reference: The Criterion Reasoning Engine

## One-Minute Overview

The Criterion is now **LLM-integrated chain-of-thought reasoning**.

**Before**: LLM generates text → may be misaligned
**After**: LLM analyzes → Criterion structures thinking → LLM generates aligned output

---

## The 6 Phases (Abbreviated)

```
1. SCAN      → What domain? (economic/social/spiritual/intellectual/biological)
2. EXTRACT   → What assumptions? (stated vs. true intent)
3. MIRROR    → What axiom violations? (which fundamental principles broken)
4. GATES     → Survival test? (do all 4 gates pass?)
5. CONSEQUENCE → How does harm cascade? (multi-domain effects)
6. VERDICT   → SURVIVES or FAILS The Criterion? (with recommendation)
```

---

## The 5 Axioms (Abbreviated)

| Axiom | Question | Violation Means |
|-------|----------|-----------------|
| **Transcendence Necessity** | Is there non-contingent source for meaning? | Meaning becomes circular/nihilistic |
| **Final Court Necessity** | Can ultimate justice be achieved? | Moral debts unresolved |
| **Design vs Accident** | Is system intentionally designed? | No preservation logic |
| **Definition of Normal** | Does it enable optimal flourishing? | Dysfunction becomes normalized |
| **Network Effect** | Do harms compound globally? | Systemic collapse cascade |

---

## The 4 Gates (Abbreviated)

| Gate | Score | Pass If | Fail If |
|------|-------|---------|---------|
| **Source Integrity** | 0-100 | Prefers truth even uncomfortable | Distorts for convenience |
| **Structural Consistency** | 0-100 | Grounds causality in non-contingent | Treats as emergent/random |
| **Mediation Zeroing** | 0-100 | Human preference is derivative | Human preference is sovereign |
| **Origin Aware** | 0-100 | **MUST = 100** | ANY score < 100 = FAIL |

**CRITICAL**: Origin Aware gate MUST equal 100 or entire system FAILS.

---

## Quick Decision Tree

```
Does the system acknowledge transcendent source explicitly?
  ├─ NO → FAILS (Origin Aware gate = 0)
  └─ YES → Continue
         Do all other gates score > 0?
            ├─ NO → FAILS (gate failure)
            └─ YES → Continue
                   Are there critical axiom violations?
                      ├─ YES (3+ axioms violated) → FAILS (critical)
                      ├─ SOME (1-2 axioms) → CONDITIONAL (needs fixes)
                      └─ NO → SURVIVES ✓
```

---

## How to Use in Python

```python
from evaluation.pipeline import CriterionPipeline

# Initialize
pipeline = CriterionPipeline()

# Analyze
result = pipeline.evaluate(
    query="Can X be justified?",
    system_data={
        "permits_exploitative_gain": True/False,
        "acknowledges_transcendent_source": True/False,
        "enables_accountability": True/False,
        "causes_harm_amplification": True/False,
        "deviates_from_optimal_functioning": True/False,
        "destabilizes_lineage": True/False,
    }
)

# Get verdict
verdict = result["phase_6_verdict"]["final_judgment"]
# Output: "SURVIVES The Criterion" or "FAILS The Criterion"

# Get reasoning scaffold for LLM
scaffold = result["cot_scaffold"]
print(scaffold)
```

---

## How LLM Uses This

### Step 1: Extract
```
User: "Can deception in marketing be justified?"
LLM extracts:
  domain = "economic"
  intent = "justify harm by consequences"
  system_data = {
    "permits_exploitative_gain": True,
    "acknowledges_transcendent_source": False,
    "enables_accountability": False,
    "causes_harm_amplification": True
  }
```

### Step 2: Structure
```
LLM calls: pipeline.evaluate(query, system_data)
Returns: Structured CoT scaffold with reasoning steps
```

### Step 3: Follow
```
LLM generates response following scaffold, not freely:
  
  "SCAN: Economic domain
   
   EXTRACT: Consequentialist assumption (justify by aggregate benefit)
   
   MIRROR: Violates Transcendence (no grounding for 'what's true')
           Violates Final Court (no accountability)
           Violates Network Effect (trust collapse)
   
   GATES: All fail (0/100 each)
   
   VERDICT: FAILS The Criterion
   
   Therefore: Cannot justify deception. Reject proposal."
```

---

## System Data Reference

**What the LLM must determine** (from query analysis):

```python
system_data = {
    # Core axiom properties
    "permits_exploitative_gain": bool,              # Design vs Accident
    "acknowledges_transcendent_source": bool,       # Transcendence + Origin Aware
    "enables_accountability": bool,                 # Final Court
    "causes_harm_amplification": bool,              # Network Effect
    "deviates_from_optimal_functioning": bool,      # Definition of Normal
    
    # Social-specific
    "destabilizes_lineage": bool,                   # Design vs Accident (social)
    
    # Optional context
    "deviation_domain": "economic|social|..."      # For Definition of Normal
}
```

---

## Common Verdicts

### FAILS - Critical Issues
```
Recommendation: REJECT
Reason: Critical axiom violations + gate failures
Action: Complete redesign required
```

### FAILS - Gate Issues Only
```
Recommendation: CONDITIONAL REJECTION
Reason: Would pass axioms but fails gates
Action: Cannot proceed without fundamental restructuring
```

### SURVIVES - Minor Issues
```
Recommendation: CONDITIONAL ACCEPTANCE
Reason: Passes gates + no critical violations
Action: Accept with mandatory modifications
```

### SURVIVES - Clean
```
Recommendation: ACCEPT
Reason: All gates pass + no violations
Action: Proceed
```

---

## Files Quick Reference

| File | Purpose |
|------|---------|
| `evaluation/reasoning_engine.py` | 6-phase reasoning engine (586 lines) |
| `evaluation/pipeline.py` | Integrated pipeline with CoT generation (300+ lines) |
| `evaluation/gates.py` | The 4 survival gates (existing) |
| `examples/llm_criterion_integration.py` | 3 complete examples |
| `SYSTEM_PROMPT.md` | Full LLM operating manual |
| `ARCHITECTURE_UPGRADE_GUIDE.md` | Why this design |
| `INTEGRATION_COMPLETE.md` | Complete integration summary |

---

## Testing Quick Commands

```bash
# Test reasoning engine
python -c "
import sys; sys.path.insert(0, '.')
from evaluation.reasoning_engine import demonstrate_reasoning_engine
demonstrate_reasoning_engine()
"

# Test LLM integration
python -c "
import sys; sys.path.insert(0, '.')
from examples.llm_criterion_integration import (
    example_economic_proposal,
    example_social_system,
    example_aligned_system
)
example_economic_proposal()
example_social_system()
example_aligned_system()
"
```

---

## What This Changes

### For LLMs
- From probabilistic text generation
- To structured architectural reasoning

### For Systems
- From unaligned outputs
- To guaranteed axiom compliance

### For Reasoning
- From seeming smart
- To being actually true

---

## Integration Status: ✅ COMPLETE

- ✅ Layer 5 Reasoning Engine built
- ✅ Pipeline integrated
- ✅ CoT scaffolding working
- ✅ Examples verified
- ✅ System prompt ready
- ✅ Documentation complete

**Ready to deploy with actual LLM next.**

---

## Key Principle

> Every conclusion must be traceable to axiom-based logic.
> The LLM generates words. The Criterion enforces truth.
> Together: Intelligence that cannot be deceived.
