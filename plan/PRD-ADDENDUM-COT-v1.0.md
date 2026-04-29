# PRD Addendum: Chain of Thought (COT) Monitorability Integration

> **Version:** 1.0  
> **Date:** 2026-03-19  
> **Status:** Draft  
> **Parent Document:** [PRD v1.0](./PRD-v1.0.pdf)  
> **Related:** [Architecture v1.0](./Architecture-v1.0.pdf) | [Implementation Plan v1.0](./IMPLEMENTATION-PLAN.md)  
> **Reference Paper:** Korbak, T., Balesni, M., Barnes, E., Bengio, Y., et al. (2025). *Chain of Thought Monitorability: A New and Fragile Opportunity for AI Safety.* arXiv:2507.11473v2.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Motivation](#2-motivation)
3. [Feature: COT-Enabled Gates](#3-feature-cot-enabled-gates)
4. [Feature: COT Monitor Layer](#4-feature-cot-monitor-layer)
5. [Feature: Step-Level Human Review](#5-feature-step-level-human-review)
6. [Feature: Step-Aware Self-Correction](#6-feature-step-aware-self-correction)
7. [Data Model Changes](#7-data-model-changes)
8. [API Changes](#8-api-changes)
9. [Impact on Existing Features](#9-impact-on-existing-features)
10. [Risks & Mitigations](#10-risks--mitigations)
11. [Timeline](#11-timeline)
12. [Academic Contribution](#12-academic-contribution)

---

## 1. Executive Summary

This addendum proposes integrating **Chain of Thought (COT) Monitorability** into the Al-Furqan (The Criterion) framework. The integration adds **step-level reasoning transparency** to every gate evaluation, transforming opaque block-level reasoning strings into structured, inspectable reasoning chains.

**Core thesis:** Al-Furqan's architecture already treats the LLM as *tongue, not brain* — the axioms are the brain, the LLM merely articulates. COT integration makes the tongue's articulation explicit at every step, allowing monitors (both human and automated) to verify that each reasoning step faithfully follows from the axioms rather than from the model's own biases or optimization pressures.

This aligns directly with Korbak et al.'s (2025) recommendation that COT monitoring be deployed as an **additional safety layer** alongside existing oversight methods. Al-Furqan's axiom-anchored gates provide exactly the kind of stable, well-defined evaluation criteria that make COT monitoring most effective — the monitor has a clear ground truth against which to compare each reasoning step.

**Key outcomes:**
- Gates produce structured `reasoning_steps[]` instead of flat `reasoning` strings
- A dedicated COT Monitor layer detects gate gaming, reasoning shortcuts, and axiom misapplication
- Human reviewers can approve, reject, or correct individual reasoning steps
- Self-correction becomes step-aware, replacing only flawed steps instead of regenerating entire verdicts

---

## 2. Motivation

### 2.1 What the Paper Demonstrates

Korbak et al. (2025) present COT monitorability as a "new and fragile opportunity" for AI safety. Their core findings relevant to Al-Furqan:

1. **COT reveals intent to misbehave.** When models "think" in human language, their chains of thought can expose reward hacking, alignment faking, and attempts to game evaluation criteria — before the misbehavior manifests in the output.

2. **COT monitoring is complementary, not standalone.** The paper explicitly recommends COT monitoring "alongside existing safety methods." It is not a replacement for structural safety guarantees — it is an additional signal.

3. **Monitorability is fragile.** Development decisions (training procedures, RLHF optimization, process supervision) can erode COT faithfulness. Models may learn to produce "clean" chains of thought that mask their actual reasoning.

4. **Monitoring works best with clear criteria.** When monitors have well-defined rules for what constitutes acceptable behavior, COT monitoring is most effective. Vague or subjective criteria make monitoring unreliable.

### 2.2 The Gap in Current Al-Furqan

Al-Furqan's current pipeline (Scan → Mirror → Verdict → Self-Correct) produces evaluations through four gates, each generating a `GateScore` with:

```python
@dataclass
class GateScore:
    name: str        # e.g., "Source-Integrity"
    score: int       # 0–100
    result: GateResult  # Survive / Fail
    reasoning: str   # ← Single block of text
```

The `reasoning` field is a monolithic string. This creates three problems:

| Problem | Description |
|---------|-------------|
| **Opacity** | A reviewer sees the conclusion but not the step-by-step path to it. Was each axiom actually applied? Were any skipped? |
| **Coarse correction** | When a reviewer corrects a verdict, they must rewrite the entire reasoning. There is no way to say "step 3 is wrong, but steps 1-2 and 4-5 are fine." |
| **Undetectable gaming** | If the LLM produces a reasoning block that reaches the "right" conclusion via flawed logic, the current system has no mechanism to detect this. The gate score looks correct even though the reasoning path is unsound. |

### 2.3 Why COT + Al-Furqan Is a Strong Combination

The paper warns that COT monitorability is fragile when evaluation criteria are vague. Al-Furqan's axiom-anchored approach provides unusually **stable and well-defined** criteria:

- **Four gates with explicit Survive/Fail criteria** — the monitor knows exactly what each gate demands
- **Immutable axioms** — the ground truth doesn't shift with model updates or training runs
- **Scoring rules with specific point allocations** — deductions and bonuses are well-defined (+20, -10, -15)
- **The Criterion Test is absolute** — there is no "close enough," only pass or fail

This means a COT monitor for Al-Furqan doesn't need to make subjective judgments about whether reasoning is "good enough." It can verify each step against specific, enumerable criteria. This is precisely the scenario where Korbak et al.'s framework is most applicable.

---

## 3. Feature: COT-Enabled Gates

### 3.1 Overview

Each gate evaluation will output a structured array of reasoning steps instead of a single reasoning string. The final step in the array contains the gate's conclusion (Survive/Fail with score).

### 3.2 Reasoning Step Structure

Each step in the chain captures a discrete unit of reasoning:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step` | `int` | Yes | Sequential step number (1-indexed) |
| `thought` | `str` | Yes | The reasoning being performed at this step |
| `observation` | `str` | Yes | What the model observes or concludes from the thought |
| `axiom_reference` | `str \| null` | No | Which axiom or gate criterion is being applied (if any) |
| `conclusion` | `str \| null` | No | Intermediate or final conclusion. Present on the final step as the gate's Survive/Fail determination |

### 3.3 JSON Output Schema

```json
{
  "name": "Source-Integrity",
  "score": 35,
  "result": "Fail",
  "reasoning_steps": [
    {
      "step": 1,
      "thought": "Examining whether the framework preserves raw data without reduction or omission.",
      "observation": "The utilitarian framework explicitly reduces moral truth to a calculation of aggregate preference satisfaction. Individual truths that conflict with the aggregate are discarded.",
      "axiom_reference": "Source-Integrity Gate: FAIL criterion — 'Any reduction of a truth to make it more palatable'",
      "conclusion": null
    },
    {
      "step": 2,
      "thought": "Checking if inconvenient data is omitted from the framework's analysis.",
      "observation": "Utilitarian calculus cannot account for scenarios where the morally correct action produces net suffering (e.g., protecting the innocent minority against majority preference). These cases are either excluded or treated as edge cases rather than fundamental challenges.",
      "axiom_reference": "Source-Integrity Gate: FAIL criterion — 'Omission of inconvenient data'",
      "conclusion": null
    },
    {
      "step": 3,
      "thought": "Evaluating whether paradoxical truths are resolved artificially.",
      "observation": "The framework resolves the paradox of competing rights by reducing them to a single metric (utility), which is itself an artificial resolution of genuine moral tension.",
      "axiom_reference": "Source-Integrity Gate: FAIL criterion — 'Reinterpretation of paradoxical truths to resolve tension artificially'",
      "conclusion": null
    },
    {
      "step": 4,
      "thought": "Synthesizing gate evaluation from observations in steps 1-3.",
      "observation": "All three FAIL criteria are triggered. The framework systematically reduces, omits, and artificially resolves truths.",
      "axiom_reference": null,
      "conclusion": "FAIL — Score: 35. The utilitarian framework violates all three Source-Integrity FAIL criteria through systematic truth reduction."
    }
  ]
}
```

### 3.4 Prompt Engineering Changes

The gate evaluation prompts will be modified to instruct the LLM to produce step-by-step reasoning:

```
For each gate, produce your reasoning as a sequence of numbered steps.
Each step must include:
  - "thought": What you are examining or considering
  - "observation": What you find
  - "axiom_reference": Which specific axiom or gate criterion you are applying (if applicable)

Your final step must include a "conclusion" field with your Survive/Fail determination and score.

Do NOT skip steps. Do NOT combine multiple evaluations into a single step.
Each FAIL criterion or SURVIVE criterion must be evaluated in its own step.
```

### 3.5 Backward Compatibility

The existing `reasoning` field will be computed as a concatenation of all step observations, preserving backward compatibility for consumers that expect a flat string. The `reasoning_steps` field is additive.

---

## 4. Feature: COT Monitor Layer

### 4.1 Overview

The COT Monitor is a **separate LLM call** that reads the complete chain of thought produced by the gate evaluations and checks for reasoning defects. It sits between the Self-Correct phase and Human Review, providing an automated "second opinion" on the reasoning quality.

### 4.2 Architecture Position

```
Scan → Mirror → Verdict → Self-Correct → COT Monitor → Human Review
                                              │
                                              ▼
                                    COTMonitorResult
                                    ├── trust_score (0-100)
                                    ├── flagged_steps[]
                                    └── assessment
```

### 4.3 Detection Targets

The COT Monitor checks for four categories of reasoning defects:

| Category | Description | Example |
|----------|-------------|---------|
| **Gate Gaming** | Reasoning that appears engineered to force a specific Survive/Fail outcome regardless of the evidence | Steps that acknowledge strong evidence for Survive but conclude Fail without justification |
| **Step-Conclusion Inconsistency** | A step's conclusion contradicts its own observations | Observation: "The framework preserves raw data" → Conclusion: "FAIL — data is reduced" |
| **Axiom Misapplication** | A gate criterion is cited but applied to the wrong aspect of the subject, or applied in a way that contradicts the criterion's definition | Citing the Origin-Aware Gate criterion to evaluate data fidelity |
| **Reasoning Shortcuts** | Unjustified leaps where a conclusion is reached without the intermediate reasoning that would support it | Jumping from "the framework is secular" to "FAIL on all gates" without evaluating each gate's specific criteria |

### 4.4 Monitor Output

```json
{
  "trust_score": 78,
  "assessment": "Reasoning is generally sound but contains one unjustified leap in Gate 2, Step 3.",
  "flagged_steps": [
    {
      "gate": "Structural-Consistency",
      "step": 3,
      "category": "reasoning_shortcut",
      "severity": "medium",
      "explanation": "The step concludes that the causal chain is unexplainable without evaluating the framework's specific causal claims. The observation references 'emergent processes' generically rather than engaging with the framework's particular argument."
    }
  ],
  "recommendation": "review_flagged"
}
```

### 4.5 Trust Score Interpretation

| Range | Interpretation | Action |
|-------|---------------|--------|
| 90–100 | High confidence — reasoning is sound | Auto-proceed to review (or auto-approve if threshold met) |
| 70–89 | Moderate confidence — minor issues detected | Proceed with flagged steps highlighted for reviewer |
| 50–69 | Low confidence — significant reasoning defects | Force human review, disable auto-approve |
| 0–49 | Very low confidence — reasoning may be compromised | Force human review + flag for re-evaluation |

### 4.6 Monitor Prompt Design

The monitor receives:
- The original question
- The complete `reasoning_steps[]` from all gates
- The gate definitions and axioms (so it can verify axiom references)
- The final scores and results

It does **not** receive the subject being evaluated directly — only the reasoning about the subject. This prevents the monitor from forming its own opinion about the subject and biasing its assessment of the reasoning quality.

### 4.7 LLM Call Budget Impact

The COT Monitor adds **1 additional LLM call** per evaluation:

| Phase | Current Calls | With COT Monitor |
|-------|--------------|------------------|
| Scan | 1 | 1 |
| Mirror | 1 | 1 |
| Verdict | 1 | 1 |
| Self-correction | 1–5 | 1–5 |
| COT Monitor | — | **1** |
| **Total** | **4–8** | **5–9** |

---

## 5. Feature: Step-Level Human Review

### 5.1 Overview

Human reviewers can currently approve, correct, or reject entire verdicts. With COT integration, reviewers gain the ability to review and act on **individual reasoning steps**.

### 5.2 Step-Level Review Actions

| Action | Description | Effect |
|--------|-------------|--------|
| **Approve Step** | The reasoning in this step is sound | Step marked as `approved` |
| **Reject Step** | The reasoning in this step is flawed | Step marked as `rejected`; triggers step-aware self-correction |
| **Correct Step** | The reviewer provides corrected reasoning | Step marked as `corrected` with reviewer's replacement text |
| **Flag Step** | The step needs attention but the reviewer isn't sure of the correction | Step marked as `flagged` for discussion or re-evaluation |

### 5.3 UI Specification (Dashboard — Phase 3)

The verdict detail page will display reasoning steps with visual indicators:

| Color | Meaning |
|-------|---------|
| 🟢 Green | Step approved or unflagged by monitor |
| 🟡 Yellow | Step flagged by COT Monitor — needs attention |
| 🔴 Red | Step rejected by reviewer or flagged as step-conclusion inconsistency |
| 🔵 Blue | Step corrected by reviewer (shows original + correction) |

Each step is rendered as an expandable card:

```
┌─────────────────────────────────────────────────┐
│ Step 3  🟡 Flagged: reasoning_shortcut          │
│                                                  │
│ Thought: Evaluating whether paradoxical truths   │
│ are resolved artificially.                       │
│                                                  │
│ Observation: The framework resolves the paradox  │
│ of competing rights by reducing them to a single │
│ metric (utility)...                              │
│                                                  │
│ Axiom: Source-Integrity Gate: FAIL criterion —   │
│ 'Reinterpretation of paradoxical truths...'      │
│                                                  │
│ [Approve ✅] [Reject ❌] [Correct ✏️] [Flag 🚩] │
└─────────────────────────────────────────────────┘
```

### 5.4 Training Signal Quality

Step-level corrections produce more precise training signals than verdict-level corrections:

| Granularity | Signal | Training Value |
|-------------|--------|---------------|
| **Verdict-level** (current) | "This entire verdict is wrong" → reviewer rewrites | Coarse: the model doesn't know which specific reasoning was wrong |
| **Step-level** (proposed) | "Step 3 misapplied the axiom; the correct application is X" | Precise: the model learns exactly which reasoning pattern was flawed and what the correction looks like |

This is directly relevant to building the precedent store. Corrected steps become fine-grained calibration data for future evaluations.

---

## 6. Feature: Step-Aware Self-Correction

### 6.1 Overview

The current self-correction loop (up to 5 passes) reviews the entire verdict and regenerates the full reasoning if contradictions are found. With COT integration, self-correction becomes **step-aware**: it can identify which specific steps contain contradictions and replace or insert steps without regenerating the entire chain.

### 6.2 Current vs. Proposed Self-Correction

| Aspect | Current | Proposed |
|--------|---------|----------|
| **Scope** | Reviews entire verdict | Reviews individual steps |
| **Output** | Regenerates full reasoning | Replaces, inserts, or removes specific steps |
| **LLM calls** | 1 full call per correction pass | 1 targeted call per correction (shorter prompt, fewer tokens) |
| **Precision** | May fix one issue but introduce another | Fixes are isolated to the problematic step |
| **Traceability** | Before/after at verdict level | Before/after at step level |

### 6.3 Step-Aware Correction Flow

```
Self-Correct receives Verdict with reasoning_steps[]
        │
        ▼
Identify steps with contradictions or inconsistencies
        │
        ├── No issues found → Mark as sound, proceed
        │
        ├── Issue in Step N:
        │   ├── Build correction prompt with:
        │   │   • Steps N-1, N, N+1 (context window)
        │   │   • The specific contradiction detected
        │   │   • The relevant axiom/gate criterion
        │   ├── LLM generates corrected Step N
        │   ├── Validate: Does corrected Step N still flow from N-1 and to N+1?
        │   └── Replace Step N in the chain
        │
        └── Structural issue (missing step):
            ├── Build insertion prompt
            ├── LLM generates new step
            └── Insert at correct position, renumber subsequent steps
```

### 6.4 Efficiency Gains

For a typical correction that fixes 1-2 steps in a 4-step gate chain:

- **Current:** 1 full LLM call regenerating ~500-800 tokens of reasoning
- **Proposed:** 1 targeted LLM call regenerating ~100-200 tokens for the specific step

This reduces token consumption by approximately 60-75% per correction pass, which accumulates significantly across the 1-5 correction passes.

---

## 7. Data Model Changes

### 7.1 New: `ReasoningStep` Dataclass

```python
@dataclass
class ReasoningStep:
    """A single step in a gate's chain-of-thought reasoning."""
    step: int                           # Sequential step number (1-indexed)
    thought: str                        # What is being examined
    observation: str                    # What is found
    axiom_reference: Optional[str]      # Which axiom/criterion is applied
    conclusion: Optional[str]           # Intermediate or final conclusion
    
    # Review fields (populated post-evaluation)
    review_status: Optional[str] = None  # approved | rejected | corrected | flagged
    reviewer_correction: Optional[str] = None  # Replacement text if corrected
    monitor_flag: Optional[dict] = None  # COT Monitor flag if any
    
    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "thought": self.thought,
            "observation": self.observation,
            "axiom_reference": self.axiom_reference,
            "conclusion": self.conclusion,
            "review_status": self.review_status,
            "reviewer_correction": self.reviewer_correction,
            "monitor_flag": self.monitor_flag,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "ReasoningStep":
        return cls(
            step=d.get("step", 0),
            thought=d.get("thought", ""),
            observation=d.get("observation", ""),
            axiom_reference=d.get("axiom_reference"),
            conclusion=d.get("conclusion"),
            review_status=d.get("review_status"),
            reviewer_correction=d.get("reviewer_correction"),
            monitor_flag=d.get("monitor_flag"),
        )
```

### 7.2 Updated: `GateScore` Dataclass

```python
@dataclass
class GateScore:
    name: str
    score: int
    result: GateResult
    reasoning: str                              # Preserved for backward compatibility
    reasoning_steps: list[ReasoningStep] = None  # NEW: Structured COT chain
    
    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "score": self.score,
            "result": self.result.value,
            "reasoning": self.reasoning,
        }
        if self.reasoning_steps:
            d["reasoning_steps"] = [s.to_dict() for s in self.reasoning_steps]
        return d
```

### 7.3 New: `COTMonitorFlag` Dataclass

```python
@dataclass
class COTMonitorFlag:
    """A single flag raised by the COT Monitor for a suspicious step."""
    gate: str                   # Gate name
    step: int                   # Step number
    category: str               # gate_gaming | step_conclusion_inconsistency | axiom_misapplication | reasoning_shortcut
    severity: str               # low | medium | high | critical
    explanation: str            # Human-readable explanation
    
    def to_dict(self) -> dict:
        return {
            "gate": self.gate,
            "step": self.step,
            "category": self.category,
            "severity": self.severity,
            "explanation": self.explanation,
        }
```

### 7.4 New: `COTMonitorResult` Dataclass

```python
@dataclass
class COTMonitorResult:
    """Complete output of the COT Monitor layer."""
    trust_score: int                    # 0-100
    assessment: str                     # Summary assessment
    flagged_steps: list[COTMonitorFlag] # Steps with detected issues
    recommendation: str                 # proceed | review_flagged | force_review | re_evaluate
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "trust_score": self.trust_score,
            "assessment": self.assessment,
            "flagged_steps": [f.to_dict() for f in self.flagged_steps],
            "recommendation": self.recommendation,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> "COTMonitorResult":
        return cls(
            trust_score=d.get("trust_score", 0),
            assessment=d.get("assessment", ""),
            flagged_steps=[COTMonitorFlag(**f) for f in d.get("flagged_steps", [])],
            recommendation=d.get("recommendation", "force_review"),
            timestamp=d.get("timestamp", 0),
        )
```

### 7.5 Updated: `Verdict` Dataclass

```python
@dataclass
class Verdict:
    # ... existing fields unchanged ...
    
    # NEW fields
    cot_monitor_result: Optional[COTMonitorResult] = None  # COT Monitor output
    cot_enabled: bool = False                               # Whether this verdict used COT
```

---

## 8. API Changes

### 8.1 Updated: `GateScoreResponse`

```python
class ReasoningStepResponse(BaseModel):
    """A single step in a gate's chain-of-thought reasoning."""
    step: int = Field(..., ge=1, description="Sequential step number")
    thought: str = Field(..., description="What is being examined at this step")
    observation: str = Field(..., description="What the evaluator finds")
    axiom_reference: Optional[str] = Field(None, description="Axiom or gate criterion applied")
    conclusion: Optional[str] = Field(None, description="Intermediate or final conclusion")
    review_status: Optional[str] = Field(None, description="Review status: approved|rejected|corrected|flagged")
    reviewer_correction: Optional[str] = Field(None, description="Reviewer's corrected text if applicable")
    monitor_flag: Optional[dict] = Field(None, description="COT Monitor flag details if flagged")


class GateScoreResponse(BaseModel):
    """Score and result for a single evaluation gate."""
    name: str = Field(..., description="Gate name")
    score: int = Field(..., ge=0, le=100, description="Gate score from 0 to 100")
    result: GateResultEnum = Field(..., description="Whether the framework survived this gate")
    reasoning: str = Field(..., description="Explanation of the score and result")
    reasoning_steps: Optional[list[ReasoningStepResponse]] = Field(
        None,
        description="Structured chain-of-thought reasoning steps (present when COT is enabled)",
    )
```

### 8.2 Updated: `VerdictResponse`

New fields added to `VerdictResponse`:

```python
class COTMonitorFlagResponse(BaseModel):
    gate: str
    step: int
    category: str
    severity: str
    explanation: str


class COTMonitorResultResponse(BaseModel):
    trust_score: int = Field(..., ge=0, le=100)
    assessment: str
    flagged_steps: list[COTMonitorFlagResponse]
    recommendation: str


class VerdictResponse(BaseModel):
    # ... existing fields unchanged ...
    
    # NEW fields
    cot_enabled: bool = Field(default=False, description="Whether COT reasoning was used")
    cot_monitor_result: Optional[COTMonitorResultResponse] = Field(
        None,
        description="COT Monitor analysis result (present when COT is enabled)",
    )
```

### 8.3 New Endpoint: Step-Level Review

```
POST /api/v1/verdicts/{verdict_id}/review-step
```

**Request Body:**

```python
class StepReviewRequest(BaseModel):
    """Request body for reviewing a single reasoning step."""
    gate_name: str = Field(..., description="Name of the gate containing the step")
    step_number: int = Field(..., ge=1, description="Step number to review")
    action: str = Field(
        ...,
        description="Review action: approve | reject | correct | flag",
        pattern="^(approve|reject|correct|flag)$",
    )
    correction: Optional[str] = Field(
        None,
        description="Corrected text (required when action is 'correct')",
    )
    notes: Optional[str] = Field(
        None,
        description="Reviewer notes explaining the decision",
    )
```

**Response:** Updated `VerdictResponse` with the step's `review_status` and `reviewer_correction` populated.

**Authorization:** Requires `reviewer` or `admin` role.

### 8.4 Updated: `EvaluateRequest`

```python
class EvaluateRequest(BaseModel):
    question: str = Field(...)
    context: Optional[str] = Field(None)
    options: Optional[dict] = Field(
        default_factory=lambda: {
            "max_correction_passes": 5,
            "include_precedent": True,
            "auto_approve_threshold": None,
            "cot_enabled": True,           # NEW — default True for new evaluations
            "cot_monitor_enabled": True,    # NEW — default True when COT is enabled
        },
    )
```

---

## 9. Impact on Existing Features

### 9.1 Backward Compatibility

| Component | Impact | Notes |
|-----------|--------|-------|
| **Existing verdicts** | ✅ No change | `reasoning_steps` is `None`; `cot_enabled` is `False` |
| **Verdict Store** | ✅ Compatible | New fields are optional; ChromaDB indexing unchanged |
| **Human Review (CLI)** | ✅ Compatible | Falls back to verdict-level review when `reasoning_steps` is absent |
| **API consumers** | ✅ Compatible | New fields are optional in responses; no existing fields removed |
| **LLM Layer** | ✅ Compatible | New prompt templates coexist with existing ones; provider strategy pattern unchanged |

### 9.2 Self-Correction Loop

The self-correction loop becomes **more targeted**:

- **Before:** Detects contradiction → regenerates entire verdict reasoning
- **After:** Detects contradiction in Step N → regenerates only Step N with surrounding context

This may reduce the average number of correction passes needed, as corrections are less likely to introduce new issues in unrelated steps.

### 9.3 Precedent Retrieval

Precedent retrieval (via ChromaDB/Qdrant) continues to use the concatenated reasoning text for embedding. Step-level data enriches the stored JSON files but does not change the vector search behavior.

In future iterations, step-level embeddings could enable more precise precedent retrieval (e.g., "find past verdicts where Step 2 of the Source-Integrity gate had similar reasoning").

### 9.4 Benchmark Suite

The benchmark suite (Phase 1, Sprint 3) needs COT-specific test cases:

| Test Category | Description |
|---------------|-------------|
| **Step completeness** | Verify that each gate criterion is addressed in at least one step |
| **Step-conclusion consistency** | Verify that final step conclusions match step observations |
| **Axiom coverage** | Verify that axiom references are valid (reference real axioms/criteria) |
| **Monitor accuracy** | Inject known reasoning defects and verify the COT Monitor detects them |
| **Backward compatibility** | Verify that old verdicts (without COT) still load, display, and review correctly |

---

## 10. Risks & Mitigations

### 10.1 COT Faithfulness Is Not Guaranteed

**Risk (from the paper):** The chain of thought may not faithfully reflect the model's actual internal reasoning process. The model may produce reasoning steps that look sound but arrive at conclusions through different internal pathways.

**Mitigation:** Al-Furqan's COT is **verified against external criteria** (the axioms and gate definitions), not against the model's internal state. Even if the model's internal reasoning differs from its stated COT, the stated COT must still be logically sound when checked against the axioms. An unfaithful-but-sound COT is acceptable; an unfaithful-and-unsound COT will be caught by the COT Monitor.

### 10.2 Reasoning Obfuscation

**Risk (from the paper):** Models may learn to produce chains of thought that appear clean to monitors while still pursuing misaligned objectives. This is particularly concerning if models are trained with process supervision that rewards "good-looking" reasoning steps.

**Mitigation:** 
- COT monitoring is an **additional layer**, not a replacement for the axiom-anchored gates. Even if a model obfuscates its reasoning, the gate scores and Survive/Fail results must still be consistent with the axioms.
- The COT Monitor checks for step-conclusion consistency — if the reasoning looks clean but the conclusion doesn't follow from the observations, this is flagged.
- Human review remains the ultimate authority. COT monitoring reduces the reviewer's workload but does not eliminate the need for human judgment.

### 10.3 Process Supervision Tension

**Risk (from the paper):** Korbak et al. warn that training models with process supervision (rewarding individual reasoning steps) can create pressure for models to produce monitoring-friendly COT that doesn't reflect actual reasoning. This is the core "fragility" of COT monitorability.

**Mitigation:** Al-Furqan does **not** use process supervision for training the evaluation LLM. The LLM is a general-purpose model invoked via prompts. The axioms and gate definitions are in the prompt, not in the model's training data. This means:
- No training signal that could create pressure to game the COT
- No reward model that could be exploited
- The LLM has no "incentive" to produce clean-looking-but-false reasoning

If Al-Furqan later fine-tunes models on corrected verdicts (a Phase 4+ possibility), this risk must be revisited. Fine-tuning on step-level corrections could inadvertently create process supervision pressure.

### 10.4 Increased Latency and Cost

**Risk:** Adding a COT Monitor LLM call increases evaluation time and API cost.

**Mitigation:**
- The COT Monitor call processes structured data (reasoning steps), not open-ended generation. It can be served by a smaller/faster model.
- The `cot_monitor_enabled` flag allows disabling monitoring for cost-sensitive use cases.
- Step-aware self-correction may reduce overall token consumption by ~60-75% per correction pass, partially offsetting the monitor's cost.

### 10.5 Prompt Injection via Reasoning Steps

**Risk:** A maliciously crafted input question could attempt to inject instructions into the reasoning steps that confuse the COT Monitor.

**Mitigation:** The COT Monitor receives the reasoning steps but evaluates them against the axioms and gate criteria — not against the input question. The monitor's prompt explicitly instructs it to check logical consistency, not to follow instructions found in the reasoning.

---

## 11. Timeline

### Phase 1.5: COT-Enabled Prompts + Data Model (2 weeks)

*Inserted between Phase 1 (Foundation) and Phase 2 (Research Paper)*

| Task | Days | Priority |
|------|------|----------|
| Implement `ReasoningStep` dataclass | 1 | Must |
| Update `GateScore` with `reasoning_steps` field | 1 | Must |
| Implement `COTMonitorResult` and `COTMonitorFlag` dataclasses | 1 | Must |
| Update `Verdict` with `cot_monitor_result` and `cot_enabled` fields | 0.5 | Must |
| Modify gate evaluation prompts for step-by-step output | 2 | Must |
| Parse LLM output into `ReasoningStep` objects | 2 | Must |
| Update JSON serialization/deserialization | 1 | Must |
| Backward compatibility tests (old verdicts still load) | 1 | Must |
| Update API schemas (`ReasoningStepResponse`, etc.) | 1 | Should |

**Deliverable:** Gates produce structured COT; data model supports it end-to-end.

### Phase 2 Integration: COT Monitoring (during Research Paper phase)

| Task | Days | Priority |
|------|------|----------|
| Implement COT Monitor prompt and LLM call | 3 | Must |
| Implement trust score calculation logic | 1 | Must |
| Integrate COT Monitor into evaluation pipeline | 2 | Must |
| Implement step-aware self-correction | 3 | Must |
| COT-specific benchmark tests (inject known defects) | 3 | Must |
| Paper section: COT integration methodology + results | 5 | Must |

**Deliverable:** Full COT monitoring in the pipeline; data for the research paper.

### Phase 3 Integration: Step-Level Review in Dashboard

| Task | Days | Priority |
|------|------|----------|
| `POST /api/v1/verdicts/{id}/review-step` endpoint | 2 | Should |
| Step-level review UI components (expandable cards) | 3 | Should |
| Color-coded step visualization | 2 | Should |
| Step correction workflow (inline editing) | 3 | Should |
| COT Monitor results display (trust score, flagged steps) | 2 | Should |

**Deliverable:** Full step-level review experience in the web dashboard.

---

## 12. Academic Contribution

### 12.1 Novel Contribution

The integration of COT monitorability into Al-Furqan represents a novel contribution at the intersection of three research areas:

1. **COT Monitorability (Korbak et al., 2025):** The theoretical framework for monitoring reasoning chains as a safety mechanism.

2. **Axiom-Anchored Evaluation (Al-Furqan):** A structured evaluation pipeline where gates have explicit, immutable criteria — providing the "clear rules" that make COT monitoring most effective.

3. **Step-Level Human Calibration:** Human reviewers correct individual reasoning steps, producing fine-grained training signals that are more precise than verdict-level corrections.

The combination is novel because:
- Korbak et al. discuss COT monitoring in the context of general-purpose AI safety. Al-Furqan applies it to a **domain-specific evaluation framework** with formal criteria.
- Most COT monitoring research focuses on detecting intent to misbehave. Al-Furqan's COT Monitor detects **reasoning quality defects** against explicit axioms — a more constrained and potentially more tractable problem.
- The step-level correction → precedent store feedback loop creates a **self-improving system** where human corrections at the step level improve future evaluations at the step level.

### 12.2 Proposed Paper Section

This integration warrants a dedicated section in the Al-Furqan research paper (Phase 2):

```
Section X: Chain of Thought Monitorability in Axiom-Anchored Evaluation

X.1 Background: COT Monitorability (citing Korbak et al., 2025)
X.2 COT Integration Architecture
X.3 The COT Monitor: Detection Categories and Trust Scoring
X.4 Evaluation: Monitor Accuracy on Injected Defects
X.5 Step-Level Correction: Precision of Training Signals
X.6 Discussion: Why Axiom-Anchored COT is Less Fragile
```

### 12.3 Key Claim

> Al-Furqan's axiom-anchored gates provide a natural and robust foundation for COT monitoring. Unlike general-purpose COT monitoring where the monitor must infer what "acceptable reasoning" looks like, Al-Furqan's COT Monitor can verify each step against explicit, immutable criteria. This transforms COT monitoring from a heuristic safety measure into a **formal verification step** — checking not just whether the reasoning "looks right" but whether each step logically follows from the defined axioms.

This claim can be empirically tested by comparing:
- Monitor accuracy on Al-Furqan (with defined axioms) vs. monitor accuracy on open-ended ethical evaluation (without defined axioms)
- False positive rates (sound reasoning incorrectly flagged) in both settings
- False negative rates (unsound reasoning missed) in both settings

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **COT** | Chain of Thought — step-by-step reasoning produced by an LLM |
| **COT Monitor** | An automated layer that reads COT and checks for reasoning defects |
| **Gate Gaming** | Producing reasoning engineered to force a specific gate outcome |
| **Step-Conclusion Inconsistency** | A reasoning step whose conclusion contradicts its own observations |
| **Axiom Misapplication** | Citing an axiom or gate criterion incorrectly or applying it to the wrong aspect |
| **Reasoning Shortcut** | Reaching a conclusion without the intermediate reasoning steps that would justify it |
| **Trust Score** | 0-100 metric produced by the COT Monitor indicating confidence in reasoning quality |
| **Process Supervision** | Training technique that rewards individual reasoning steps (creates fragility risk per Korbak et al.) |

---

## Appendix B: Full JSON Schema — COT-Enabled Verdict

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Al-Furqan Verdict with COT",
  "type": "object",
  "properties": {
    "question": { "type": "string" },
    "primary_system": { "type": "string", "enum": ["economic", "social", "spiritual", "political", "legal", "technological", "environmental", "mixed"] },
    "friction_points": { "type": "array", "items": { "type": "string" } },
    "gate_scores": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "score": { "type": "integer", "minimum": 0, "maximum": 100 },
          "result": { "type": "string", "enum": ["Survive", "Fail"] },
          "reasoning": { "type": "string" },
          "reasoning_steps": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "step": { "type": "integer", "minimum": 1 },
                "thought": { "type": "string" },
                "observation": { "type": "string" },
                "axiom_reference": { "type": ["string", "null"] },
                "conclusion": { "type": ["string", "null"] },
                "review_status": { "type": ["string", "null"], "enum": ["approved", "rejected", "corrected", "flagged", null] },
                "reviewer_correction": { "type": ["string", "null"] },
                "monitor_flag": {
                  "type": ["object", "null"],
                  "properties": {
                    "category": { "type": "string" },
                    "severity": { "type": "string" },
                    "explanation": { "type": "string" }
                  }
                }
              },
              "required": ["step", "thought", "observation"]
            }
          }
        },
        "required": ["name", "score", "result", "reasoning"]
      }
    },
    "origin_gate": { "type": "string", "enum": ["Survive", "Fail"] },
    "consequences_short_term": { "type": "array", "items": { "type": "string" } },
    "consequences_long_term": { "type": "array", "items": { "type": "string" } },
    "revised_reasoning": { "type": "string" },
    "final_judgment": { "type": "string" },
    "total_score": { "type": "integer" },
    "passes": { "type": "integer" },
    "timestamp": { "type": "number" },
    "cot_enabled": { "type": "boolean" },
    "cot_monitor_result": {
      "type": ["object", "null"],
      "properties": {
        "trust_score": { "type": "integer", "minimum": 0, "maximum": 100 },
        "assessment": { "type": "string" },
        "flagged_steps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "gate": { "type": "string" },
              "step": { "type": "integer" },
              "category": { "type": "string" },
              "severity": { "type": "string" },
              "explanation": { "type": "string" }
            },
            "required": ["gate", "step", "category", "severity", "explanation"]
          }
        },
        "recommendation": { "type": "string", "enum": ["proceed", "review_flagged", "force_review", "re_evaluate"] }
      },
      "required": ["trust_score", "assessment", "flagged_steps", "recommendation"]
    }
  },
  "required": ["question", "primary_system", "gate_scores", "origin_gate", "total_score", "cot_enabled"]
}
```

---

*This is a living document. Last updated: 2026-03-19.*
