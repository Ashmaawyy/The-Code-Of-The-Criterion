# Reasoning Engine — Technical Reference

**File:** `reasoning_engine.py`
**Role:** The constitutional core of the system. Defines all axioms, gates, prompt templates, data structures, and the evaluation pipeline.

## 1. Data Structures

### SystemType (Enum)

Classifies the domain of the input question.

| Value | Description |
|-------|-------------|
| `economic` | Markets, finance, trade, monetary policy |
| `social` | Community, culture, norms, family |
| `spiritual` | Religion, metaphysics, purpose, meaning |
| `political` | Governance, power, law, policy |
| `legal` | Justice system, rights, regulation |
| `technological` | Technology, AI, engineering, digital systems |
| `environmental` | Ecology, resources, climate |
| `mixed` | Cross-domain or unclassifiable (fallback) |

### GateResult (Enum)

Binary outcome for each gate evaluation.

| Value | Meaning |
|-------|---------|
| `Survive` | The subject passes this gate's criteria |
| `Fail` | The subject violates this gate's criteria |

### GateScore (Dataclass)

A single gate's evaluation result.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Gate name (e.g., "Source-Integrity") |
| `score` | `int` | 0–100 numeric score |
| `result` | `GateResult` | Survive or Fail |
| `reasoning` | `str` | LLM's explanation for this score |

**Methods:**
- `to_dict() -> dict` — Serializes to a plain dictionary.

### Verdict (Dataclass)

The complete output of a single evaluation.

| Field | Type | Description |
|-------|------|-------------|
| `question` | `str` | The original input question |
| `primary_system` | `SystemType` | Identified domain |
| `friction_points` | `list[str]` | Deviations from axioms identified during scan |
| `gate_scores` | `list[GateScore]` | Tri-axial gate results (3 gates) |
| `origin_gate` | `GateResult` | Origin-Aware gate result (Survive/Fail only) |
| `consequences_short_term` | `list[str]` | Immediate consequences |
| `consequences_long_term` | `list[str]` | Compounded/systemic consequences |
| `revised_reasoning` | `str` | Final reasoning aligned with axioms |
| `final_judgment` | `str` | Decisive verdict statement |
| `total_score` | `int` | Aggregate alignment score |
| `passes` | `int` | Number of self-correction passes run |
| `timestamp` | `float` | Unix timestamp, auto-set on creation |

**Methods:**
- `to_dict() -> dict` — Serializes all fields to a plain dictionary. Enums are stored as their string values. Gate scores are serialized as a list of dicts.
- `from_dict(d: dict) -> Verdict` — Class method. Reconstructs a Verdict from a dictionary (e.g., loaded from a JSON file). Handles missing keys with safe defaults, coerces string scores to integers, and falls back to `SystemType.MIXED` for unrecognized system types.
- `to_log() -> str` — Returns a human-readable plain-text formatted log string.

## 2. Immutable Constants (The Constitution)

These are defined as module-level string constants and embedded into every LLM prompt.

| Constant | Content |
|----------|---------|
| `FRAMEWORK_PREAMBLE` | System identity and role statement |
| `AXIOMS` | Transcendence Necessity Proof, Final Court Necessity Proof, Core Axioms |
| `GATE_DEFINITIONS` | Full definitions of all 4 gates with Survive/Fail criteria |
| `SCORING_RULES` | Point allocation rules (+20, -10, -15, gate ranges, origin bonus) |

These constants are never modified at runtime. They are the constitutional foundation of every evaluation.

## 3. Prompt Builders

Four functions that construct structured prompts for each phase. Each includes the full axioms and relevant context.

### build_scan_prompt(question, context)

**Purpose:** Phase 1 — The Scan.
**Inputs:** User question + optional prior verdict context.
**Instructs LLM to produce:**

```json
{
    "primary_system": "<system type>",
    "immediate_effects": ["..."],
    "network_effects": ["..."],
    "friction_points": ["..."]
}
```

### build_mirror_prompt(question, scan_result)

**Purpose:** Phase 2 — The Mirror.
**Inputs:** Question + scan results.
**Instructs LLM to produce:**

```json
{
    "gate_1_source_integrity": {"score": 0-100, "result": "Survive/Fail", "reasoning": "..."},
    "gate_2_structural_consistency": {"score": 0-100, "result": "Survive/Fail", "reasoning": "..."},
    "gate_3_mediation_zeroing": {"score": 0-100, "result": "Survive/Fail", "reasoning": "..."},
    "gate_4_origin_aware": {"score": 0-100, "result": "Survive/Fail", "reasoning": "..."},
    "contradictions_found": ["..."],
    "axiom_alignment_notes": "..."
}
```

### build_verdict_prompt(question, scan_result, mirror_result)

**Purpose:** Phase 3 — The Verdict.
**Inputs:** Question + scan + mirror results.
**Instructs LLM to produce:**

```json
{
    "consequences_short_term": ["..."],
    "consequences_long_term": ["..."],
    "actors_and_mechanisms": "...",
    "revised_reasoning": "...",
    "final_judgment": "...",
    "total_score": <integer>
}
```

### build_correction_prompt(question, current_verdict, pass_number)

**Purpose:** Self-correction pass.
**Inputs:** Question + current verdict + pass number.
**Instructs LLM to produce:**

```json
{
    "contradictions_found": ["..."],
    "is_sound": true/false,
    "corrected_verdict": null or {full verdict object}
}
```

## 4. ReasoningEngine Class

### Constructor

```python
ReasoningEngine(llm_call: Callable[[str], str])
```

Accepts any callable that takes a string prompt and returns a string response. This is the only interface between the reasoning engine and the LLM layer.

### Class Attribute

- `MAX_CORRECTION_PASSES: int = 5` — Maximum self-correction iterations. Can be overridden via config.

### Public Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `scan(question, context)` | Runs Phase 1 | `dict` (parsed JSON) |
| `mirror(question, scan_result)` | Runs Phase 2 | `dict` (parsed JSON) |
| `verdict(question, scan_result, mirror_result)` | Runs Phase 3 | `dict` (parsed JSON) |
| `self_correct(question, current_verdict, pass_number)` | Runs one correction pass | `dict` (parsed JSON) |
| `evaluate(question, context)` | Full pipeline: all phases + correction loop | `Verdict` object |

### Internal Methods

| Method | Description |
|--------|-------------|
| `_parse_json(raw)` | Extracts JSON from LLM response. Handles markdown code fences, surrounding text, and locates JSON boundaries via brace matching. |
| `_build_gate_scores(mirror_result)` | Converts raw mirror dict into a list of 4 `GateScore` objects. Coerces scores to `int`. |
| `_build_verdict_object(question, scan, mirror, verdict, passes)` | Constructs a `Verdict` from raw phase results. Separates tri-axial gates (first 3) from origin gate (4th). Coerces system type and score to safe types. |

### Evaluation Pipeline Flow

```
evaluate(question, context)
    │
    ├── scan(question, context)           → scan_result dict
    ├── mirror(question, scan_result)     → mirror_result dict
    ├── verdict(question, scan, mirror)   → verdict_result dict
    │
    ├── for i in 1..MAX_CORRECTION_PASSES:
    │   ├── self_correct(question, verdict_result, i)
    │   ├── if sound: break
    │   └── if corrected: verdict_result = corrected
    │
    └── _build_verdict_object(...)        → Verdict
```
