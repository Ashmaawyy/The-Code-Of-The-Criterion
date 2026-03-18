# The Code of The Criterion (Al-Furqan)

An AI reasoning engine that evaluates ideas, policies, and behaviors through a structured, axiom-anchored framework. The system implements a multi-gate evaluation pipeline with self-correction, precedent-based learning via vector storage, and human-in-the-loop oversight.

## The Problem

Large Language Models reason from training data distributions — they have no fixed axioms, no consistency across sessions, and no mechanism to build on past judgments. They drift, contradict themselves, and treat all frameworks as equally valid.

This project builds a reasoning layer on top of any LLM that enforces:

- **Axiomatic anchoring** — all reasoning derives from immutable logical necessities, not opinion
- **Multi-gate verification** — every output must survive four independent consistency checks
- **Self-correction** — iterative contradiction resolution before any verdict is finalized
- **Precedent memory** — past verdicts inform future reasoning through semantic retrieval
- **Human calibration** — a human-in-the-loop approves, corrects, or rejects verdicts

## Philosophical Foundation

The framework is built on two logical proofs and three core axioms:

### Transcendence Necessity Proof

1. If something exists, it must have a purpose (design necessarily implies purpose — purposeless design is a logical contradiction).
2. Only mechanisms can be explained logically.
3. Purpose cannot be explained logically without a Transcendent source.

### Final Court Necessity Proof

1. Objective moral obligations create real moral debts.
2. Real moral debts require just resolution; otherwise, justice is incomplete.
3. Human justice systems are contingent — constrained by knowledge, power, and lifespan.
4. Many moral violations remain unresolved at death.
5. If all accountability ends at death, moral debts remain permanently unresolved.
6. A system with permanently unresolved moral debts cannot constitute complete justice.
7. **Conclusion:** Complete justice requires a final, non-contingent court with perfect knowledge, authority over all agents, and power to enact irreversible judgment.

### Core Axioms

- **Design vs. Accident** — Complexity and functional order cannot arise purely by chance. The world, humanity, and societal systems are designed with operational purposes.
- **Definition of Normal** — Normal behavior is that which aligns with optimal human functioning (life, intellect, lineage, societal stability). Deviations are abnormal if they compromise systemic well-being, even if common or socially accepted.
- **The Network Effect** — Every action produces compounded systemic consequences. Analysis must consider both local and global effects on mankind.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   User Input                     │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│              Verdict Store (RAG)                 │
│         Retrieve relevant prior verdicts         │
└──────────────────────┬──────────────────────────┘
                       │ context
                       ▼
┌─────────────────────────────────────────────────┐
│            Reasoning Engine Pipeline             │
│                                                  │
│  ┌───────────┐  ┌───────────┐  ┌─────────────┐ │
│  │  Phase 1   │  │  Phase 2   │  │   Phase 3   │ │
│  │  THE SCAN  │→ │ THE MIRROR │→ │ THE VERDICT │ │
│  │            │  │            │  │             │ │
│  │ Identify   │  │ Gate 1:    │  │ Consequences│ │
│  │ system     │  │  Source    │  │ Actors &    │ │
│  │ type,      │  │  Integrity │  │ mechanisms  │ │
│  │ effects,   │  │ Gate 2:    │  │ Revised     │ │
│  │ friction   │  │  Structural│  │ reasoning   │ │
│  │ points     │  │  Consist.  │  │ Final       │ │
│  │            │  │ Gate 3:    │  │ judgment    │ │
│  │            │  │  Mediation │  │ Score       │ │
│  │            │  │  Zeroing   │  │             │ │
│  │            │  │ Gate 4:    │  │             │ │
│  │            │  │  Origin-   │  │             │ │
│  │            │  │  Aware     │  │             │ │
│  └───────────┘  └───────────┘  └──────┬──────┘ │
│                                        │        │
│                    ┌───────────────────┘        │
│                    ▼                             │
│  ┌──────────────────────────────────────┐       │
│  │     Self-Correction Loop (≤5 passes) │       │
│  │     Until no contradictions remain   │       │
│  └──────────────────────────────────────┘       │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│               Structured Verdict                 │
│  Question, System, Friction Points, Gate Scores, │
│  Consequences, Reasoning, Judgment, Score        │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│             Human-in-the-Loop Review             │
│         Approve / Correct / Reject               │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│              Verdict Store (Write)               │
│    Approved/corrected → indexed for retrieval    │
│    Rejected → logged but excluded from index     │
└─────────────────────────────────────────────────┘
```

## The Four Gates

Every evaluation must survive all four gates. A failure in any gate flags the verdict for deeper analysis.

| Gate | Name | Tests For | Fails If |
|------|------|-----------|----------|
| 1 | **Source-Integrity** | Data fidelity — is raw truth preserved? | Omits, reduces, or reinterprets truth for convenience |
| 2 | **Structural-Consistency** | Causal mapping — can the system be explained without luck? | Treats moral order as emergent without a non-contingent source |
| 3 | **Mediation-Zeroing** | Human noise audit — is human cognition treated as finite? | Relies on human preference or secular humanism as foundation |
| 4 | **Origin-Aware** | Source recognition — does truth trace to a transcendent source? | Treats truth as emergent or contingent |

## Scoring

- **+20** per correctly identified friction or alignment with axioms
- **-10** per contradiction or misalignment with gates
- **-15** for unjustified neutrality (no void space — every position is a position)
- **-15** for avoidance of consequence deduction
- **Gate scores:** 0-100 per gate
- **Origin-Aware Gate:** Survive = +20 bonus
- Only full-score frameworks pass The Criterion Test

## Project Structure

```
The-Code-Of-The-Criterion/
├── README.md               # This file
├── requirements.txt        # Python dependencies (core + optional)
├── config.py               # Central configuration — YAML-based with defaults
├── reasoning_engine.py     # The Criterion framework — gates, scoring, pipeline
├── llm_layer.py            # LLM integration — Ollama, Transformers, OpenAI-compatible
├── verdict_store.py        # ChromaDB vector storage — precedent retrieval
├── human_review.py         # Human-in-the-loop CLI — approve, correct, reject
├── main.py                 # CLI entry point — interactive + batch modes
└── verdicts/               # Persistent verdict JSON logs
```

## Component Interactions

```
config.py ──────────────────────────────────────┐
  │ AppConfig (LLM, Engine, Store, Review)      │
  ▼                                              │
main.py ◄── entry point                         │
  │  builds all components from config           │
  │                                              │
  ├──► llm_layer.py                              │
  │     │  create_llm(config) → LLMProvider      │
  │     │  Provider.__call__(prompt) → str       │
  │     ▼                                        │
  ├──► reasoning_engine.py                       │
  │     │  ReasoningEngine(llm_call)             │
  │     │  .evaluate(question, context) → Verdict│
  │     │  Scan → Mirror → Verdict → Correct     │
  │     ▼                                        │
  ├──► verdict_store.py                          │
  │     │  VerdictStore(chroma_dir, verdicts_dir)│
  │     │  .store(verdict) / .retrieve(question) │
  │     │  .invalidate_cascade(id) → flagged[]   │
  │     ▼                                        │
  └──► human_review.py                           │
        │  HumanReview(store)                    │
        │  .review_verdict(verdict) → verdict_id │
        │  .browse_verdicts() / .search_verdicts()
        └────────────────────────────────────────┘
```

## How It Works

### 1. The Scan
The system identifies the domain (economic, social, spiritual, political, legal, technological, environmental) and maps immediate and network-level effects. Friction points — deviations from the core axioms — are flagged.

### 2. The Mirror
The subject is evaluated through all four gates independently. Each gate produces a score (0-100) and a Survive/Fail result with reasoning. Contradictions between gates are identified.

### 3. The Verdict
Consequences are deduced (short-term and long-term). Actors and mechanisms are stated. Reasoning is revised to align deductively with the axioms. A decisive judgment is delivered.

### 4. Self-Correction
The verdict is iteratively reviewed for contradictions, misalignments, unjustified neutrality, or avoidance of consequence deduction. Up to 5 passes run until no contradictions remain.

### 5. Human Review
The human reviewer can approve (verdict is indexed for future precedent), correct (original is superseded, corrected version is indexed), or reject (verdict is logged but excluded from the index).

### 6. Precedent Accumulation
Over time, the system builds a body of verdicts — its case law. New evaluations retrieve semantically similar past verdicts as context, enabling the reasoning engine to build on established precedent rather than reasoning from scratch.

## The Learning Mechanism

The system gets smarter through a feedback loop:

1. **Early stage** — The human corrects frequently. The verdict store is sparse.
2. **Growth stage** — Corrections decrease as precedent coverage grows. The system retrieves relevant past verdicts and builds on them.
3. **Maturity stage** — The human shifts from corrector to auditor, only intervening on genuinely novel cases. The system has a rich body of internally consistent precedent.

Bad verdicts can be retroactively invalidated. When a verdict is invalidated, the system flags all later verdicts that may have been influenced by it for re-review (`invalidate_cascade`). Flagged verdicts are removed from the search index until re-approved by the human reviewer.

## Design Principles

- **The axioms are the constitution** — immutable, never modified at runtime
- **The verdicts are case law** — growing, building precedent
- **The reasoning patterns are legal principles** — emergent from accumulated rulings
- **The human is the appeals court** — corrective, not generative
- **The gates are procedural safeguards** — structural, enforced on every evaluation
- **The LLM is the tongue** — provides language capability, not truth

## Key Design Decisions

- **LLM-agnostic:** The reasoning engine accepts any callable with signature `llm_call(prompt: str) -> str`. Three providers are included: Ollama (local, recommended), HuggingFace Transformers (local, supports quantization), and any OpenAI-compatible API.
- **Dual storage:** Verdicts are stored in both ChromaDB (for semantic search) and JSON files (for human-readable audit trail).
- **Rejected verdicts are preserved but not indexed:** They remain in the file system for audit but are excluded from the vector index so they never pollute future reasoning.
- **Index consistency:** When a verdict's status changes (approved, rejected, needs_review), the ChromaDB index is updated accordingly. Re-approved verdicts are re-indexed; flagged verdicts are removed from search until reviewed.
- **No unjustified neutrality:** There is no void space in the human world — claiming neutrality is itself a position. The system is penalized for avoiding a verdict when one is logically necessitated.
- **Verdict deserialization:** Verdicts can be reconstructed from stored JSON via `Verdict.from_dict()`, enabling re-processing and re-evaluation of past verdicts.

## Installation

```bash
# Clone the repository
git clone https://github.com/ashmaawyy/The-Code-Of-The-Criterion.git
cd The-Code-Of-The-Criterion

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install core dependencies
pip install -r requirements.txt

# Install Ollama (recommended LLM provider)
# Download from https://ollama.com then:
ollama pull mistral
```

### Optional: HuggingFace Transformers Provider

```bash
pip install torch transformers
# For quantization (Linux only):
pip install bitsandbytes
```

## Usage

### Interactive Mode

```bash
python main.py
```

Enter any question at the prompt to evaluate it. Available commands:

| Command | Description |
|---------|-------------|
| `/review` | Open the human review session |
| `/stats` | Show verdict store statistics |
| `/search` | Semantic search over past verdicts |
| `/llm` | Show LLM call statistics |
| `/config` | Show current configuration |
| `/quit` | Exit |

### Command-Line Options

```bash
python main.py --init              # Generate default config.yaml
python main.py --evaluate "..."    # Evaluate a single question
python main.py --review            # Open human review session
python main.py --stats             # Show verdict store statistics
python main.py -c path/to/config   # Use custom config file
```

### Configuration

Run `python main.py --init` to generate a `config.yaml` with all options documented. Key settings:

```yaml
llm:
  provider: ollama              # ollama | transformers | openai_compatible
  model_name: mistral           # model to use
  temperature: 0.1              # low for deterministic reasoning

engine:
  max_correction_passes: 5      # self-correction iterations

store:
  collection_name: criterion_verdicts

review:
  auto_approve_threshold: null  # set to integer (e.g. 90) to skip review for high scores
```

## Requirements

- Python 3.10+
- **Core:** chromadb, requests, pyyaml
- **LLM (pick one):**
  - Ollama (recommended) — local, simple setup
  - HuggingFace Transformers — local, supports 4bit/8bit quantization
  - Any OpenAI-compatible API — LM Studio, vLLM, Together.ai, Groq

### Recommended Models

| Model | Size | Strengths |
|-------|------|-----------|
| mistral | 7B | Fast, good reasoning for its size |
| llama3.1 | 8B | Strong instruction following |
| qwen2.5 | 7B/14B | Excellent structured JSON output |
| deepseek-r1 | 7B | Strong reasoning capabilities |
| gemma3 | 12B | Good balance of speed and quality |

## Status

- [x] Reasoning engine — full pipeline with gates, scoring, and self-correction
- [x] Verdict store — ChromaDB vector storage with semantic retrieval and cascade invalidation
- [x] Human review interface — CLI for approving, correcting, and rejecting verdicts
- [x] LLM layer — Ollama, Transformers, and OpenAI-compatible providers
- [x] Configuration — YAML-based with defaults and generation
- [x] CLI entry point — interactive and batch evaluation modes
- [x] Requirements — documented core and optional dependencies
- [ ] Test suite

## License

This project is open source. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome. The axioms are immutable by design — contributions should improve the architecture, not modify the philosophical foundation.
