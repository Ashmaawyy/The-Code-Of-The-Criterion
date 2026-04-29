# System Architecture

This document describes the complete architecture of Al-Furqan: how the components are structured, how they interact, and how data flows through the system.

## 1. High-Level Overview

The system has five layers, each with a distinct role:

```
┌─────────────────────────────┐
│       CLI / Entry Point     │  main.py
│   (User interface layer)    │
├─────────────────────────────┤
│      Human Review Layer     │  human_review.py
│   (Appeals court / QA)      │
├─────────────────────────────┤
│    Reasoning Engine Layer   │  reasoning_engine.py
│  (The Criterion framework)  │
├─────────────────────────────┤
│     Verdict Store Layer     │  verdict_store.py
│  (Memory / precedent / RAG) │
├─────────────────────────────┤
│        LLM Layer            │  llm_layer.py
│  (Language generation)      │
├─────────────────────────────┤
│     Configuration Layer     │  config.py
│  (Settings for all layers)  │
└─────────────────────────────┘
```

## 2. Component Roles

| Component | Role | Metaphor |
|-----------|------|----------|
| `reasoning_engine.py` | Defines the axioms, gates, prompts, and evaluation pipeline | The Constitution |
| `verdict_store.py` | Stores verdicts, retrieves precedent by semantic similarity | The Memory / Case Law |
| `human_review.py` | Allows humans to approve, correct, or reject verdicts | The Appeals Court |
| `llm_layer.py` | Provides language generation from any LLM provider | The Tongue |
| `config.py` | Centralizes all settings for all components | The Settings Registry |
| `main.py` | Assembles components and provides the user interface | The Orchestrator |

## 3. Dependency Graph

```
config.py
  │
  ├──imports──► llm_layer.py (LLMConfig)
  │
main.py
  │
  ├──imports──► config.py (AppConfig, load_config, generate_default_config)
  ├──imports──► llm_layer.py (create_llm, LLMProvider)
  ├──imports──► reasoning_engine.py (ReasoningEngine, Verdict)
  ├──imports──► verdict_store.py (VerdictStore)
  └──imports──► human_review.py (HumanReview, display_verdict, run_review_session)

human_review.py
  │
  ├──imports──► reasoning_engine.py (Verdict, GateScore, GateResult)
  └──imports──► verdict_store.py (VerdictStore)

verdict_store.py
  │
  ├──imports──► reasoning_engine.py (Verdict, GateResult, SystemType, GateScore)
  └──imports──► chromadb (third-party)

reasoning_engine.py
  │
  └── (no internal project imports — foundational module)

llm_layer.py
  │
  └── (no internal project imports — foundational module)
```

**Foundational modules** (no project dependencies): `reasoning_engine.py`, `llm_layer.py`
**Mid-level modules**: `verdict_store.py`, `config.py`, `human_review.py`
**Top-level orchestrator**: `main.py`

## 4. Data Flow — Full Evaluation Cycle

```
User enters question
        │
        ▼
┌─ main.py: run_evaluation() ─────────────────────────────────┐
│                                                              │
│  1. verdict_store.retrieve_as_context(question)              │
│     └─► Returns formatted string of similar past verdicts    │
│                                                              │
│  2. reasoning_engine.scan(question, context)                 │
│     ├─► Builds scan prompt (axioms + question + context)     │
│     ├─► Calls LLM                                           │
│     └─► Returns: {primary_system, effects, friction_points}  │
│                                                              │
│  3. reasoning_engine.mirror(question, scan_result)           │
│     ├─► Builds mirror prompt (axioms + gates + scan data)    │
│     ├─► Calls LLM                                           │
│     └─► Returns: {gate scores, contradictions, alignment}    │
│                                                              │
│  4. reasoning_engine.verdict(question, scan, mirror)         │
│     ├─► Builds verdict prompt (all data combined)            │
│     ├─► Calls LLM                                           │
│     └─► Returns: {consequences, reasoning, judgment, score}  │
│                                                              │
│  5. Self-correction loop (up to 5 passes)                    │
│     ├─► Builds correction prompt with current verdict        │
│     ├─► Calls LLM                                           │
│     ├─► If sound: break                                      │
│     └─► If contradictions: apply corrections, loop           │
│                                                              │
│  6. Build Verdict object from raw results                    │
│                                                              │
│  7. Auto-approve (if score >= threshold) OR human review     │
│     ├─► human_review.review_verdict(verdict)                 │
│     └─► Returns: approve / correct / reject                  │
│                                                              │
│  8. verdict_store.store(verdict, status)                     │
│     ├─► Saves JSON file to verdicts/                         │
│     └─► Indexes in ChromaDB (if approved/corrected)          │
└──────────────────────────────────────────────────────────────┘
```

## 5. LLM Calls Per Evaluation

A single evaluation makes a minimum of **4 LLM calls** and a maximum of **8 LLM calls**:

| Phase | Calls | Purpose |
|-------|-------|---------|
| Scan | 1 | Identify system type, effects, friction points |
| Mirror | 1 | Evaluate through all 4 gates |
| Verdict | 1 | Deduce consequences, deliver judgment |
| Self-correction | 1–5 | Iterative contradiction resolution |
| **Total** | **4–8** | |

## 6. Storage Architecture

### Dual Storage Strategy

Every verdict is stored in two places:

**ChromaDB (Vector Database)**
- Purpose: Semantic similarity search for precedent retrieval
- Content: Embedded text document combining question, reasoning, and judgment
- Metadata: System type, gate scores, total score, status, timestamp
- Indexed: Only `approved` and `corrected` verdicts
- Location: `.chroma_db/` directory

**JSON Files (File System)**
- Purpose: Human-readable audit trail, backup, full data preservation
- Content: Complete verdict data including all fields
- Indexed: All verdicts regardless of status
- Location: `verdicts/` directory
- Naming: `verdict_{timestamp}.json`

### Index Consistency Rules

| Status Change | ChromaDB Action |
|---------------|-----------------|
| New `approved` | Upsert to index |
| New `corrected` | Upsert to index |
| New `rejected` | Not indexed |
| Changed to `rejected` | Delete from index |
| Changed to `needs_review` | Delete from index |
| Changed to `approved` (re-approval) | Re-upsert to index |
| Changed to `superseded` | Delete from index |

## 7. Configuration Hierarchy

```
config.yaml (file on disk)
    │
    ▼
load_config() parses YAML
    │
    ▼
AppConfig (master dataclass)
    ├── LLMConfig      → passed to create_llm()
    ├── EngineConfig    → applied to ReasoningEngine.MAX_CORRECTION_PASSES
    ├── StoreConfig     → passed to VerdictStore constructor
    └── ReviewConfig    → read by main.py for auto-approve threshold
```

If `config.yaml` does not exist, all values fall back to hardcoded defaults. The system works with zero configuration.
