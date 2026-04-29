# Al-Furqan (الفرقان) — The Criterion
<!-- markdownlint-disable MD040 -->

> Axiom-Anchored Neuro-Symbolic Reasoning Engine with Tafsir Knowledge Base

Al-Furqan is a **general-purpose reasoning engine** that evaluates ideas, systems, and claims against immutable logical axioms through formal verification. It uses the Islamic Knowledge Base as its verified reference point — because the axioms themselves establish this as the only source that passes all four survival gates.

**Key principle:** The Code guides. The LLM thinks. Z3 proves. The Knowledge Base knows.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                   Al-Furqan                      │
├─────────────────────────────────────────────────┤
│  Layer 4: API & Orchestration                    │
│  ├── REST API (FastAPI)                          │
│  └── Tafsir RAG Pipeline (Engine-Guided)         │
├─────────────────────────────────────────────────┤
│  Layer 3: Furqan Engine                          │
│  ├── 4 Axioms (immutable)                        │
│  ├── 4 Survival Gates                            │
│  ├── Guided Reasoning Chains                     │
│  ├── Symbolic Verification (Z3 SMT)              │
│  ├── Reasoning-as-a-Skill (RaaS)                 │
│  └── Tafsir Reasoning (Axiom-Guided Templates)   │
├─────────────────────────────────────────────────┤
│  Layer 2: Knowledge Base                         │
│  ├── Quran (114 surahs, 6,236 verses)            │
│  ├── Hadith (Bukhari, Muslim, graded)            │
│  ├── Fiqh Rules (major/minor)                    │
│  ├── Tafsir KB (Sheikh Ahmad Al-Sayyid)          │
│  ├── Knowledge Graph (verse relationships)       │
│  └── Embeddings (MiniLM / CamelBERT)            │
├─────────────────────────────────────────────────┤
│  Layer 1: Storage (Elasticsearch)                │
│  ├── 6 ES Indices (quran, hadith, graph, etc.)   │
│  ├── Verdict Store (ES)                          │
│  └── Feedback Store (ES)                         │
└─────────────────────────────────────────────────┘
```

---

## 🎯 The Four Gates

Every claim passes through 4 sequential survival gates:

| Gate | Name | Criterion |
| ------ | ------ | ----------- |
| 1 | **Source-Integrity** | Is raw truth preserved without reduction? |
| 2 | **Structural-Consistency** | Can the system explain causality without luck? |
| 3 | **Mediation-Zeroing** | Is human cognition treated as finite, not authoritative? |
| 4 | **Origin-Aware** | Does truth trace to a transcendent source? |

---

## 🧠 Engine-Guided Tafsir RAG Pipeline

A complete pipeline for Quranic reasoning that teaches the LLM **how to think**, not just what to answer:

```
User Question
      ↓
① Query Analyzer          — extracts verses, topics, question type
      ↓
② Reasoning Plan Builder  — LLM selects Axioms & Gates dynamically
      ↓
③ LLM Execution           — thinks + searches KB with tools
      ↓
④ Human Feedback           — 4 verdicts (✅/✅📝/❌/❌📝)
```

### KB Tools (exposed to LLM via function calling)

- `search_kb_by_verse("6:5")` — all edges for a verse
- `search_kb_by_topic("السنة الإلهية")` — semantic topic search
- `search_kb_by_relation("6:5", "LINKED_HADITH")` — specific relation type
- `get_verse_context("6:5", range=3)` — surrounding verses + KB data

### Reasoning Templates

6 templates, each mapped to relevant Axioms + Gates:
`TAFSIR` · `VERSE_LINK` · `ISTINBAT` · `COMPARISON` · `SEERAH_LINK` · `GENERAL`

### Knowledge Base

> The KB is **not limited to Tafsir** — Tafsir was the first use case to validate the pipeline. The KB is designed to absorb any verified knowledge source (Hadith sciences, Fiqh, Aqeedah, Seerah, Arabic language, Maqasid, contemporary scholarship, etc.)

- **First use case:** مدارسة سورة الأنعام — الشيخ أحمد السيد (23 episodes)
- **Extraction:** Whisper transcription → chunk → LLM extraction → human review
- **Current:** 67 entries (Episode 1), central verses: 6:1, 6:5
- **Structure:** Central verse → linked verses, hadiths, concepts, tafsir
- **Expandable:** Same pipeline works for any scholarly source

---

## 🔬 Symbolic Verification

Z3 SMT solver provides formal mathematical proofs for:

- Transcendence Necessity Proof
- Final Court Necessity Proof
- Axiom consistency verification

---

## 📊 Test Coverage

```
705 tests total
├── Engine (gates, chains, pipeline, axioms, Z3)     ~560
├── Knowledge Base (quran, hadith, fiqh, graph)       ~60
├── Tafsir RAG Pipeline                               100
│   ├── Query Analyzer                                 23
│   ├── KB Tools                                       17
│   ├── Tool Executor                                  13
│   ├── Reasoning Plan Builder                         22
│   ├── Pipeline (end-to-end)                          13
│   └── Feedback System                                12
├── RaaS (Reasoning-as-a-Skill)                        31
├── Memory (MCP server)                                56
└── Security (prompt guard, audit, sandbox)            ~30
```

---

## 🛡️ Security

5-layer defense-in-depth:

1. **Prompt Guard** — injection detection + sanitization
2. **Axiom Integrity** — SHA-256 hash verification (immutable)
3. **Output Validator** — response filtering
4. **Adapter Sandbox** — isolated LLM execution
5. **Audit Logger** — hashed question logging

---

## 📁 Project Structure

```
al-furqan/
├── src/al_furqan/
│   ├── engine/                    # Furqan Engine
│   │   ├── axioms.py              # Immutable axioms + gates
│   │   ├── pipeline.py            # Scan → Mirror → Verdict
│   │   ├── chains/                # Guided reasoning chains
│   │   ├── gates/                 # 4 survival gates
│   │   ├── symbolic/              # Z3 formal verification
│   │   ├── security/              # 5-layer security
│   │   └── tafsir/                # Tafsir reasoning pipeline
│   │       ├── axiom_selector.py  # Dynamic axiom/gate selection
│   │       ├── reasoning_plan_builder.py
│   │       ├── reasoning_templates.py
│   │       ├── pipeline.py        # End-to-end RAG pipeline
│   │       └── feedback.py        # Human feedback system
│   ├── kb/                        # Knowledge Base
│   │   ├── es/                    # Elasticsearch backend
│   │   │   ├── collections.py     # Quran, Hadith collections
│   │   │   ├── graph.py           # ES-backed knowledge graph
│   │   │   ├── retriever.py       # Unified retriever
│   │   │   └── indices.py         # 6 index definitions
│   │   ├── graph/                 # Graph schema
│   │   ├── ingestion/             # Transcript → KB extraction
│   │   └── tafsir/                # Tafsir KB tools
│   │       ├── query_analyzer.py  # Question analysis
│   │       ├── kb_tools.py        # 4 search tools for LLM
│   │       └── tool_executor.py   # Tool call execution
│   ├── tokenizer/                 # Multi-level Quran tokenizer
│   │   ├── encoder.py             # 5-level tokenization pipeline
│   │   ├── schema.py              # Token dataclasses
│   │   ├── morphology.py          # QAC-aware root extraction
│   │   └── semantics.py           # Semantic + logic + transitions
│   ├── providers/                 # LLM providers (Ollama, DashScope, Anthropic, etc.)
│   ├── store/                     # Verdict + feedback storage (ES-backed)
│   └── api/                       # REST API
├── data/
│   ├── quran/                     # Complete Quran text
│   ├── hadith/                    # Hadith collections
│   ├── tafsir/                    # 9 Arabic tafsir books (consolidated)
│   ├── lessons/                   # Transcribed episodes
│   ├── review/                    # Proposed edges (KB)
│   ├── benchmark/                 # Evaluation results
│   └── tafsir_feedback/           # Human feedback entries
├── furqan-raas/                   # Reasoning-as-a-Skill (MCP)
├── furqan-memory/                 # Memory system (MCP)
├── tests/                         # 705 tests
├── scripts/                       # Processing & evaluation scripts
│   ├── eval/                      #   Engine evaluation & A/B testing
│   ├── ingestion/                 #   Data prep & KB ingestion
│   ├── benchmarks/                #   KB & embedding benchmarks
│   ├── kb_extraction/             #   Lesson → knowledge graph
│   └── rendering/                 #   Architecture docs to PDF/PNG
└── docs/                          # Documentation
```

---

## 📚 Documentation

See [docs/README.md](docs/README.md) for the full index. Key documents:

| Document | Description |
| ---------- | ------------- |
| [Architecture v3.0](docs/active_docs/AL-FURQAN-ARCHITECTURE-v3.0.md) | Complete system architecture |
| [Project Status](docs/active_docs/PROJECT-STATUS.md) | Current state, what's done, what's planned |
| [Elasticsearch Migration](docs/active_docs/ELASTICSEARCH-MIGRATION.md) | ChromaDB/JSON → ES migration |
| [Quran Tokenizer](docs/active_docs/QURAN-TOKENIZER-v1.0.md) | 5-level tokenizer (Word → Root → Semantic → Logic → Transition) |
| [RAG Implementation Plan](docs/active_docs/RAG-IMPLEMENTATION-PLAN-v1.0.md) | Engine-Guided RAG pipeline design |
| [Fine-Tuning Plan](docs/active_docs/FINE-TUNING-IMPLEMENTATION-PLAN-v1.0.md) | SFT + DPO plan for Furqan-27B |
| [Security Policy](docs/active_docs/FURQAN-AXIOM-SECURITY-POLICY-v1.0.md) | 5-layer security architecture |
| [RaaS Docs](docs/active_docs/FURQAN-RAAS-DOCS.md) | Reasoning-as-a-Skill |

---

## 🚀 Roadmap

### ✅ Done

- [x] Furqan Engine (4 gates, reasoning chains, Z3 verification)
- [x] Knowledge Base (Quran, Hadith, Fiqh, 9 Tafsir books)
- [x] Knowledge Graph (transcript extraction, central verse tracking)
- [x] Security (5-layer defense, axiom integrity)
- [x] Engine-Guided RAG Pipeline (query analysis → reasoning plan → LLM + tools → feedback)
- [x] Human Feedback System (4 verdicts, full context storage)
- [x] Dynamic Axiom/Gate Selection (LLM chooses from raw Engine definitions)
- [x] Elasticsearch migration (all core storage — 6 indices with Arabic analyzer)
- [x] Multi-level Quran Tokenizer (5 levels: Word → Root → Semantic → Logic → Transition)
- [x] Lesson pipeline (24 episodes, 2,487 training pairs)
- [x] 705 tests passing

### 🔜 Next

- [ ] Download & process episodes 2-23 (KB expansion)
- [ ] Collect 500+ human-reviewed pipeline responses
- [ ] Semantic search API endpoint (ES backend ready)
- [ ] Cross-verse transition analysis

### 🔮 Future

- [ ] Fine-tune Furqan-27B (SFT + DPO on Qwen3.5-27B-Claude-Opus-Distilled)
- [ ] Local deployment (vLLM/SGLang)
- [ ] Multi-scholar KB support
- [ ] QLP v3.0 integration (Local-First)

---

## 🛠️ Tech Stack

| Layer | Technology |
| ------- | ----------- |
| Language | Python 3.12 |
| LLM Providers | DashScope (Qwen), Anthropic, Ollama, OpenAI-compatible |
| Formal Verification | Z3 SMT Solver |
| Embeddings | MiniLM / CamelBERT |
| Storage (Core) | Elasticsearch 8.13 (6 indices, custom Arabic analyzer) |
| Storage (Memory Skill) | SQLite + ChromaDB (client-side, local-only) |
| API | FastAPI |
| Testing | pytest (705 tests) |
| Transcription | OpenAI Whisper |
| Tokenizer | 5-level Quran tokenizer (Word, Root, Semantic, Logic, Transition) |
| Future Training | LLaMA-Factory + Unsloth (LoRA/QLoRA) |

---

## 📄 License

Apache 2.0

---

*Al-Furqan: The Code guides. The LLM thinks. Z3 proves. The Knowledge Base knows.*
