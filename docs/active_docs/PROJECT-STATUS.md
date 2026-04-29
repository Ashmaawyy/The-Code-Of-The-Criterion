# Al-Furqan Project Status

**Last updated:** April 7, 2026
**Branch:** `dev`
**Source files:** 106 Python modules | **Test files:** 43 modules

---

## Completed Work

### Core Engine (Sprints 1-6) — Done

| Component | Status | Tests | Notes |
|-----------|--------|-------|-------|
| 4 Immutable Axioms | Done | SHA-256 integrity verified | `engine/axioms.py` |
| 4 Survival Gates | Done | ~120 | Independent, deterministic scoring |
| 16 Guided Reasoning Chains | Done | ~20 | 3-4 questions per gate |
| Z3 Symbolic Verification | Done | ~20 | Formal proofs for axioms + gate consistency |
| Scan-Mirror-Verdict Pipeline | Done | ~30 | Dual-perspective evaluation |
| 5-Layer Security | Done | ~70 | IntegrityVerifier, PromptGuard, OutputValidator, AdapterSandbox, AuditLogger |

### Knowledge Base — Done

| Component | Status | Tests | Notes |
|-----------|--------|-------|-------|
| Quran (6,236 verses) | Done | — | Sourced from Tanzil, indexed in ES |
| Hadith (38,016+) | Done | — | Bukhari, Muslim, graded collections |
| Fiqh (50+ rules) | Done | — | Core rules extracted |
| Tafsir KB (Episode 1) | Done | — | 67 entries, central verses 6:1/6:5 |
| Knowledge Graph (ES) | Done | ~60 | Edges linking verses, hadiths, concepts |
| HuggingFace Quran-Tafseer | Done | — | 9 Arabic tafsir books consolidated |

### Elasticsearch Migration (Mar 30) — Done

All core engine storage migrated from ChromaDB/JSON to Elasticsearch:
- 10 indices: 9 RAG + 1 training (820K docs, ~1.8 GB)
- Custom `arabic_furqan` analyzer with 6 character filters
- `dense_vector` fields for embeddings
- Docker Compose auto-seeding via `es-seed` service (idempotent upsert)
- See [ELASTICSEARCH-MIGRATION.md](ELASTICSEARCH-MIGRATION.md)

### Engine-Guided RAG Pipeline (Sprint RAG, Mar 22) — Done

| Component | Tests | Notes |
|-----------|-------|-------|
| Query Analyzer | 23 | Arabic verse/topic extraction |
| KB Tools (4 search tools) | 17 | Exposed to LLM via function calling |
| Tool Executor | 13 | Tool call execution + validation |
| Reasoning Plan Builder | 22 | Dynamic axiom/gate selection |
| Pipeline (end-to-end) | 13 | Full orchestration |
| Feedback System | 12 | 4 verdicts (correct/correct_notes/wrong/wrong_notes) |

### Multi-Level Quran Tokenizer — Done

5-level tokenization with certainty=1.0 ground truth:

| Level | Token | Purpose |
|-------|-------|---------|
| 1 | WordToken | Surface form in mushaf order |
| 2A | RootToken | Trilateral root + morphological pattern |
| 2B | SemanticToken | Semantic field + pattern meaning + syntactic role |
| 2C | LogicToken | Logical operators + argument structure |
| 3 | TransitionToken | Idea-to-idea flow + transition types |

**Phonetic/tajweed layer deliberately removed** (Apr 3) — mimicking the Quran is forbidden; the training signal teaches logical structure and idea transitions.

Reward weights: `word=0.10, root=0.20, semantic=0.20, logic=0.25, transition=0.25`

### MCP Skills — Done

| Skill | Tests | Tools | Status |
|-------|-------|-------|--------|
| RaaS (furqan-raas/) | 31 | 5 (evaluate, verify, retrieve, explain, domains) | Production |
| Memory (furqan-memory/) | 56 | 5 (remember, recall, recognize, feedback, stats) | Production |

### Lesson Pipeline — Done

- 24 episodes of Surat Al-An'am transcribed (Whisper)
- 3-stage pipeline: clean → enrich → train
- 2,487 training pairs generated
- All indexed into Elasticsearch (`furqan_lessons`)

### REST API — Done

FastAPI with authentication (bcrypt + API keys), rate limiting, 6 routers:
`/evaluate`, `/verdicts`, `/criterion`, `/review`, `/stats`, `/health`

---

## In Progress

| Item | Status | Notes |
|------|--------|-------|
| Documentation reorganization | In progress | Splitting docs/ into active_docs/ and legacy_docs/ |

---

## Planned (Not Started)

### Near-Term

| Item | Dependency | Notes |
|------|-----------|-------|
| KB expansion (Episodes 2-23) | Transcripts available | Same pipeline as Episode 1, 22 episodes remaining |
| 500+ human-reviewed responses | Pipeline usage | Needed for fine-tuning data collection |
| Semantic search API endpoint | ES ready | Backend supports it, need to expose via API |
| Cross-verse transition analysis | Tokenizer | Detect transitions spanning multiple verses |

### Future

| Item | Dependency | Notes |
|------|-----------|-------|
| Fine-tune Furqan-27B | 500+ SFT examples, 300+ DPO pairs | SFT + DPO on Qwen3.5-27B-Claude-Opus-Distilled |
| Local deployment | Fine-tuned model | vLLM/SGLang serving |
| Multi-scholar KB | KB pipeline | Extend beyond Sheikh Ahmad Al-Sayyid |
| QLP v3.0 integration | Architecture | Local-First + digital sovereignty |
| Transition pattern library | Tokenizer maturity | Catalog recurring Quranic transition patterns |
| Passage-level reasoning classification | Cross-verse analysis | Assign ReasoningPattern at ruku/passage level |

---

## Infrastructure

| Component | Technology | Status |
|-----------|-----------|--------|
| Language | Python 3.12 | Active |
| Backend storage | Elasticsearch 8.13 | Active (10 indices, ~1.8 GB) |
| LLM providers | Anthropic Claude, DashScope Qwen, Ollama | Active |
| Formal verification | Z3 SMT Solver | Active |
| Embeddings | MiniLM / CamelBERT | Active |
| API framework | FastAPI | Active |
| Testing | pytest | 43 test modules |
| Transcription | OpenAI Whisper | Used for lesson processing |
| Future training | LLaMA-Factory + Unsloth (LoRA/QLoRA) | Planned |

---

## Key Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Mar 19 | Project inception | First session, 44K documents integrated |
| Mar 20 | Architecture v2.0 approved | Sprint 2 complete (205 tests) |
| Mar 21 | Sprints 3-6 executed in single day | 647 tests delivered |
| Mar 22 | RAG pipeline sprint | 100 additional tests |
| Mar 30 | ChromaDB → Elasticsearch migration | Unified backend, Arabic-native analysis |
| Mar 30 | Multi-level tokenizer implemented | 5 levels, certainty=1.0 ground truth |
| Apr 3 | Phonetic layer removed | Mimicking Quran forbidden; focus on logical transitions |
| Apr 3 | TransitionToken added | Captures idea-to-idea flow as core training signal |
| Apr 7 | Template Q&A training data removed | Replaced with clean ayah→tafsir pairs (188K); Docker auto-seed added |

---

_Al-Furqan: The Code guides. The LLM thinks. Z3 proves. The Knowledge Base knows._
