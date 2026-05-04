# Al-Furqan (الفرقان) — The Criterion

> Axiom-Anchored Neuro-Symbolic Reasoning Engine with Tafsir Knowledge Base

---

## The Problem

Most AI systems reason by pattern-matching across probability distributions. They aggregate, they hedge, they produce outputs calibrated to what "most sources say." This works for many tasks — but it has a structural flaw: **there is no fixed ground**.

When truth is treated as emergent from data, every conclusion is provisional. Causality becomes correlation. Authority becomes consensus. And the system has no principled way to distinguish a sound argument from a plausible-sounding one.

Al-Furqan is built on a different premise: that **logical necessity, not statistical likelihood**, should govern reasoning. It evaluates ideas, systems, and claims against four immutable axioms through formal verification — using the Islamic Knowledge Base as its verified reference point, because those axioms themselves establish it as the only source that passes all four survival gates.

---

## 🚀 Quick Start

```bash
# 1. Clone and install
git clone https://github.com/your-org/al-furqan.git
cd al-furqan
pip install -e ".[dev]"

# 2. Start Elasticsearch (required for KB and storage)
docker-compose up -d elasticsearch

# 3. Configure your LLM provider
cp .env.example .env
# Set ANTHROPIC_API_KEY, DASHSCOPE_API_KEY, or OLLAMA_HOST

# 4. Start the API
uvicorn src.al_furqan.api.main:app --reload

# 5. Run your first query
curl -X POST http://localhost:8000/reason \
  -H "Content-Type: application/json" \
  -d '{"question": "What does verse 6:5 establish about human cognition?"}'
```

Run the full test suite:

```bash
pytest tests/ -v  # 705 tests
```

---

## 🏗️ Architecture

<svg width="700" height="465" viewBox="0 0 700 465" xmlns="http://www.w3.org/2000/svg">
  <rect width="700" height="465" rx="10" fill="#0d1117"/>
  <text x="350" y="28" text-anchor="middle" fill="#f0f6fc" font-size="14" font-weight="bold" font-family="system-ui, sans-serif" letter-spacing="0.3">Al-Furqan — System Architecture</text>

  <!-- LAYER 4: API -->
  <rect x="20" y="45" width="660" height="75" rx="6" fill="#161b22" stroke="#1f6feb" stroke-width="1.5"/>
  <rect x="20" y="45" width="7" height="75" rx="3" fill="#1f6feb"/>
  <text x="38" y="62" fill="#58a6ff" font-size="9.5" font-weight="bold" letter-spacing="1.5" font-family="monospace">LAYER 4</text>
  <text x="110" y="62" fill="#e6edf3" font-size="12" font-weight="600" font-family="system-ui, sans-serif">API &amp; Orchestration</text>
  <text x="38" y="81" fill="#6e7681" font-size="11" font-family="monospace">&#x251C;&#x2500;&#x2500; REST API (FastAPI)</text>
  <text x="38" y="97" fill="#6e7681" font-size="11" font-family="monospace">&#x2514;&#x2500;&#x2500; Tafsir RAG Pipeline (Engine-Guided)</text>

  <!-- LAYER 3: Engine -->
  <rect x="20" y="130" width="660" height="130" rx="6" fill="#161b22" stroke="#388bfd" stroke-width="1.5"/>
  <rect x="20" y="130" width="7" height="130" rx="3" fill="#388bfd"/>
  <text x="38" y="147" fill="#79c0ff" font-size="9.5" font-weight="bold" letter-spacing="1.5" font-family="monospace">LAYER 3</text>
  <text x="110" y="147" fill="#e6edf3" font-size="12" font-weight="600" font-family="system-ui, sans-serif">Furqan Engine</text>
  <text x="38" y="167" fill="#6e7681" font-size="11" font-family="monospace">&#x251C;&#x2500;&#x2500; 4 Axioms (immutable)</text>
  <text x="38" y="183" fill="#6e7681" font-size="11" font-family="monospace">&#x251C;&#x2500;&#x2500; 4 Survival Gates</text>
  <text x="38" y="199" fill="#6e7681" font-size="11" font-family="monospace">&#x251C;&#x2500;&#x2500; Guided Reasoning Chains</text>
  <text x="38" y="215" fill="#6e7681" font-size="11" font-family="monospace">&#x251C;&#x2500;&#x2500; Symbolic Verification (Z3 SMT)</text>
  <text x="38" y="231" fill="#6e7681" font-size="11" font-family="monospace">&#x251C;&#x2500;&#x2500; Reasoning-as-a-Skill (RaaS)</text>
  <text x="38" y="247" fill="#6e7681" font-size="11" font-family="monospace">&#x2514;&#x2500;&#x2500; Tafsir Reasoning (Axiom-Guided Templates)</text>

  <!-- LAYER 2: Knowledge Base (two-column) -->
  <rect x="20" y="270" width="660" height="120" rx="6" fill="#161b22" stroke="#3fb950" stroke-width="1.5"/>
  <rect x="20" y="270" width="7" height="120" rx="3" fill="#3fb950"/>
  <text x="38" y="287" fill="#56d364" font-size="9.5" font-weight="bold" letter-spacing="1.5" font-family="monospace">LAYER 2</text>
  <text x="110" y="287" fill="#e6edf3" font-size="12" font-weight="600" font-family="system-ui, sans-serif">Knowledge Base</text>
  <text x="38" y="307" fill="#6e7681" font-size="11" font-family="monospace">&#x251C;&#x2500;&#x2500; Quran (114 surahs, 6,236 verses)</text>
  <text x="38" y="323" fill="#6e7681" font-size="11" font-family="monospace">&#x251C;&#x2500;&#x2500; Fiqh Rules (major / minor)</text>
  <text x="38" y="339" fill="#6e7681" font-size="11" font-family="monospace">&#x2514;&#x2500;&#x2500; Knowledge Graph (verse relationships)</text>
  <line x1="362" y1="300" x2="362" y2="352" stroke="#21262d" stroke-width="1"/>
  <text x="373" y="307" fill="#6e7681" font-size="11" font-family="monospace">&#x251C;&#x2500;&#x2500; Hadith (Bukhari, Muslim, graded)</text>
  <text x="373" y="323" fill="#6e7681" font-size="11" font-family="monospace">&#x251C;&#x2500;&#x2500; Tafsir KB (Sheikh Ahmad Al-Sayyid)</text>
  <text x="373" y="339" fill="#6e7681" font-size="11" font-family="monospace">&#x2514;&#x2500;&#x2500; Embeddings (MiniLM / CamelBERT)</text>

  <!-- LAYER 1: Storage -->
  <rect x="20" y="400" width="660" height="50" rx="6" fill="#161b22" stroke="#a371f7" stroke-width="1.5"/>
  <rect x="20" y="400" width="7" height="50" rx="3" fill="#a371f7"/>
  <text x="38" y="418" fill="#bc8cff" font-size="9.5" font-weight="bold" letter-spacing="1.5" font-family="monospace">LAYER 1</text>
  <text x="110" y="418" fill="#e6edf3" font-size="12" font-weight="600" font-family="system-ui, sans-serif">Storage (Elasticsearch 8.13)</text>
  <text x="38" y="438" fill="#6e7681" font-size="11" font-family="monospace">6 indices &#xB7; custom Arabic analyzer &#xB7; Verdict Store &#xB7; Feedback Store</text>
</svg>

---

## 🎯 The Four Survival Gates

Every claim — regardless of source, eloquence, or tradition — must pass four sequential gates. A claim that fails any gate is rejected, not hedged.

| Gate | Name | Criterion |
|------|------|-----------|
| 1 | **Source-Integrity** | Is raw truth preserved without reduction? |
| 2 | **Structural-Consistency** | Can the system explain causality without luck? |
| 3 | **Mediation-Zeroing** | Is human cognition treated as finite, not authoritative? |
| 4 | **Origin-Aware** | Does truth trace to a transcendent source? |

**What failure looks like at each gate:**

- **Gate 1 failure:** The system selectively quotes, paraphrases, or reframes the source — changing the claim in the process of transmitting it. Any lossy compression of truth fails here.
- **Gate 2 failure:** The system can describe what happened but not *why*. Correlations presented as causes, outcomes attributed to chance, or circular explanations all fail here.
- **Gate 3 failure:** Human reasoning, consensus, or authority is treated as a terminal source rather than an instrument. The moment a scholar's opinion becomes unfalsifiable, Gate 3 collapses.
- **Gate 4 failure:** The reasoning chain terminates at a contingent origin — a text, a tradition, a person — rather than tracing to a transcendent, self-sufficient source. Systems that bottom out at "because we decided so" fail here.

---

## 🧠 Engine-Guided Tafsir RAG Pipeline

A complete pipeline for Quranic reasoning that teaches the LLM **how to think**, not just what to answer:

<svg width="580" height="400" viewBox="0 0 580 400" xmlns="http://www.w3.org/2000/svg">
  <rect width="580" height="400" rx="10" fill="#0d1117"/>
  <text x="290" y="28" text-anchor="middle" fill="#f0f6fc" font-size="13" font-weight="bold" font-family="system-ui, sans-serif">Engine-Guided RAG Pipeline</text>

  <!-- Input pill -->
  <rect x="190" y="42" width="200" height="34" rx="17" fill="#21262d" stroke="#30363d" stroke-width="1.5"/>
  <text x="290" y="64" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="system-ui, sans-serif">User Question</text>

  <!-- Arrow 1 -->
  <line x1="290" y1="76" x2="290" y2="88" stroke="#484f58" stroke-width="2"/>
  <polygon points="283,86 297,86 290,96" fill="#484f58"/>

  <!-- Step 1 -->
  <rect x="90" y="96" width="400" height="54" rx="6" fill="#161b22" stroke="#1f6feb" stroke-width="1.5"/>
  <rect x="90" y="96" width="6" height="54" rx="3" fill="#1f6feb"/>
  <text x="108" y="115" fill="#58a6ff" font-size="10" font-weight="bold" letter-spacing="1" font-family="monospace">&#x2460; QUERY ANALYZER</text>
  <text x="108" y="135" fill="#6e7681" font-size="11" font-family="system-ui, sans-serif">Extracts verses, topics, and question type</text>

  <!-- Arrow 2 -->
  <line x1="290" y1="150" x2="290" y2="162" stroke="#484f58" stroke-width="2"/>
  <polygon points="283,160 297,160 290,170" fill="#484f58"/>

  <!-- Step 2 -->
  <rect x="90" y="170" width="400" height="54" rx="6" fill="#161b22" stroke="#388bfd" stroke-width="1.5"/>
  <rect x="90" y="170" width="6" height="54" rx="3" fill="#388bfd"/>
  <text x="108" y="189" fill="#79c0ff" font-size="10" font-weight="bold" letter-spacing="1" font-family="monospace">&#x2461; REASONING PLAN BUILDER</text>
  <text x="108" y="209" fill="#6e7681" font-size="11" font-family="system-ui, sans-serif">LLM selects Axioms and Gates dynamically</text>

  <!-- Arrow 3 -->
  <line x1="290" y1="224" x2="290" y2="236" stroke="#484f58" stroke-width="2"/>
  <polygon points="283,234 297,234 290,244" fill="#484f58"/>

  <!-- Step 3 -->
  <rect x="90" y="244" width="400" height="54" rx="6" fill="#161b22" stroke="#3fb950" stroke-width="1.5"/>
  <rect x="90" y="244" width="6" height="54" rx="3" fill="#3fb950"/>
  <text x="108" y="263" fill="#56d364" font-size="10" font-weight="bold" letter-spacing="1" font-family="monospace">&#x2462; LLM EXECUTION</text>
  <text x="108" y="283" fill="#6e7681" font-size="11" font-family="system-ui, sans-serif">Reasons and searches KB with tools</text>

  <!-- Arrow 4 -->
  <line x1="290" y1="298" x2="290" y2="310" stroke="#484f58" stroke-width="2"/>
  <polygon points="283,308 297,308 290,318" fill="#484f58"/>

  <!-- Step 4 -->
  <rect x="90" y="318" width="400" height="54" rx="6" fill="#161b22" stroke="#f78166" stroke-width="1.5"/>
  <rect x="90" y="318" width="6" height="54" rx="3" fill="#f78166"/>
  <text x="108" y="337" fill="#ffa198" font-size="10" font-weight="bold" letter-spacing="1" font-family="monospace">&#x2463; HUMAN FEEDBACK</text>
  <text x="108" y="357" fill="#6e7681" font-size="11" font-family="system-ui, sans-serif">4 verdicts: approved / approved+note / rejected / rejected+note</text>
</svg>

### KB Tools (exposed to LLM via function calling)

| Tool | Description |
|------|-------------|
| `search_kb_by_verse("6:5")` | All knowledge graph edges for a verse |
| `search_kb_by_topic("السنة الإلهية")` | Semantic topic search across the KB |
| `search_kb_by_relation("6:5", "LINKED_HADITH")` | Filter by specific relation type |
| `get_verse_context("6:5", range=3)` | Surrounding verses + all KB data |

### Reasoning Templates

Six templates, each dynamically mapped to relevant Axioms and Gates by the LLM at query time:

`TAFSIR` · `VERSE_LINK` · `ISTINBAT` · `COMPARISON` · `SEERAH_LINK` · `GENERAL`

---

## 📚 Knowledge Base

The KB is not limited to Tafsir. **Tafsir is the first validated use case for a general-purpose verified-knowledge framework.** The same ingestion pipeline — transcription → chunking → LLM extraction → human review — is designed to absorb any verified scholarly source: Hadith sciences, Fiqh, Aqeedah, Seerah, Arabic language, Maqasid, contemporary scholarship, and beyond.

**Current state:**
- **First use case:** مدارسة سورة الأنعام — الشيخ أحمد السيد (23 episodes)
- **Ingestion pipeline:** Whisper transcription → chunk → LLM extraction → human review
- **Loaded:** 67 entries (Episode 1), central verses: 6:1, 6:5
- **Structure:** Central verse → linked verses, hadiths, concepts, tafsir nodes
- **Coverage:** 9 Arabic Tafsir books consolidated, 24 episodes transcribed, 2,487 training pairs

---

## 🔬 Symbolic Verification

Z3 SMT solver provides formal mathematical proofs — not heuristics, not confidence scores — for:

- Transcendence Necessity Proof
- Final Court Necessity Proof
- Axiom consistency verification

Formal verification means the engine can distinguish between a claim that is *probably true* and one that is *necessarily true*. That distinction is the foundation of the entire system.

---

## 🛡️ Security

5-layer defense-in-depth:

| Layer | Component | Function |
|-------|-----------|----------|
| 1 | **Prompt Guard** | Injection detection + sanitization |
| 2 | **Axiom Integrity** | SHA-256 hash verification — axioms are immutable |
| 3 | **Output Validator** | Response filtering before delivery |
| 4 | **Adapter Sandbox** | Isolated LLM execution environment |
| 5 | **Audit Logger** | Hashed question logging for traceability |

---

## 📊 Test Coverage

<svg width="580" height="285" viewBox="0 0 580 285" xmlns="http://www.w3.org/2000/svg">
  <rect width="580" height="285" rx="10" fill="#0d1117"/>
  <text x="290" y="26" text-anchor="middle" fill="#f0f6fc" font-size="13" font-weight="bold" font-family="system-ui, sans-serif">Test Coverage — 705 Tests</text>

  <!-- Engine ~560: bar_width = (560/560)*355 = 355 -->
  <text x="168" y="65" text-anchor="end" fill="#8b949e" font-size="11" font-family="system-ui, sans-serif">Engine</text>
  <rect x="175" y="50" width="355" height="24" rx="4" fill="#1f6feb"/>
  <text x="538" y="67" fill="#e6edf3" font-size="11" font-family="monospace">~560</text>

  <!-- Tafsir Pipeline 100: (100/560)*355 = 63 -->
  <text x="168" y="103" text-anchor="end" fill="#8b949e" font-size="11" font-family="system-ui, sans-serif">Tafsir Pipeline</text>
  <rect x="175" y="88" width="63" height="24" rx="4" fill="#388bfd"/>
  <text x="246" y="105" fill="#e6edf3" font-size="11" font-family="monospace">100</text>

  <!-- Memory 56: (56/560)*355 = 36 -->
  <text x="168" y="141" text-anchor="end" fill="#8b949e" font-size="11" font-family="system-ui, sans-serif">Memory</text>
  <rect x="175" y="126" width="36" height="24" rx="4" fill="#a371f7"/>
  <text x="219" y="143" fill="#e6edf3" font-size="11" font-family="monospace">56</text>

  <!-- KB ~60: (60/560)*355 = 38 -->
  <text x="168" y="179" text-anchor="end" fill="#8b949e" font-size="11" font-family="system-ui, sans-serif">Knowledge Base</text>
  <rect x="175" y="164" width="38" height="24" rx="4" fill="#3fb950"/>
  <text x="221" y="181" fill="#e6edf3" font-size="11" font-family="monospace">~60</text>

  <!-- RaaS 31: (31/560)*355 = 20 -->
  <text x="168" y="217" text-anchor="end" fill="#8b949e" font-size="11" font-family="system-ui, sans-serif">RaaS</text>
  <rect x="175" y="202" width="20" height="24" rx="4" fill="#e3b341"/>
  <text x="203" y="219" fill="#e6edf3" font-size="11" font-family="monospace">31</text>

  <!-- Security ~30: (30/560)*355 = 19 -->
  <text x="168" y="255" text-anchor="end" fill="#8b949e" font-size="11" font-family="system-ui, sans-serif">Security</text>
  <rect x="175" y="240" width="19" height="24" rx="4" fill="#f78166"/>
  <text x="202" y="257" fill="#e6edf3" font-size="11" font-family="monospace">~30</text>
</svg>

---

## 🚀 Roadmap

### ✅ Complete

- Furqan Engine (4 gates, reasoning chains, Z3 verification)
- Knowledge Base (Quran, Hadith, Fiqh, 9 Tafsir books)
- Knowledge Graph (transcript extraction, central verse tracking)
- Security (5-layer defense, axiom integrity)
- Engine-Guided RAG Pipeline (query analysis → reasoning plan → LLM + tools → feedback)
- Human Feedback System (4 verdicts, full context storage)
- Dynamic Axiom/Gate Selection (LLM selects from raw Engine definitions)
- Elasticsearch migration (all core storage — 6 indices with Arabic analyzer)
- Multi-level Quran Tokenizer (5 levels: Word → Root → Semantic → Logic → Transition)
- Lesson pipeline (24 episodes, 2,487 training pairs)
- 705 tests passing

### 🔜 Next (Near-Term)

- [ ] Multi-scholar KB support — expand beyond Sheikh Ahmad Al-Sayyid
- [ ] QLP v3.0 integration (Local-First)
- [ ] Local deployment (vLLM / SGLang)

### 🔮 Horizon

- [ ] Fine-tune Furqan-27B (SFT + DPO on Qwen3.5-27B-Claude-Opus-Distilled)

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
│   │       ├── axiom_selector.py
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
│   │       ├── query_analyzer.py
│   │       ├── kb_tools.py        # 4 search tools for LLM
│   │       └── tool_executor.py
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
├── scripts/
│   ├── eval/                      # Engine evaluation & A/B testing
│   ├── ingestion/                 # Data prep & KB ingestion
│   ├── benchmarks/                # KB & embedding benchmarks
│   ├── kb_extraction/             # Lesson → knowledge graph
│   └── rendering/                 # Architecture docs to PDF/PNG
└── docs/                          # Documentation
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
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

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture v3.0](docs/active_docs/AL-FURQAN-ARCHITECTURE-v3.0.md) | Complete system architecture |
| [Project Status](docs/active_docs/PROJECT-STATUS.md) | Current state, what's done, what's planned |
| [Elasticsearch Migration](docs/active_docs/ELASTICSEARCH-MIGRATION.md) | ChromaDB/JSON → ES migration |
| [Quran Tokenizer](docs/active_docs/QURAN-TOKENIZER-v1.0.md) | 5-level tokenizer design |
| [RAG Implementation Plan](docs/active_docs/RAG-IMPLEMENTATION-PLAN-v1.0.md) | Engine-Guided RAG pipeline design |
| [Fine-Tuning Plan](docs/active_docs/FINE-TUNING-IMPLEMENTATION-PLAN-v1.0.md) | SFT + DPO plan for Furqan-27B |
| [Security Policy](docs/active_docs/FURQAN-AXIOM-SECURITY-POLICY-v1.0.md) | 5-layer security architecture |
| [RaaS Docs](docs/active_docs/FURQAN-RAAS-DOCS.md) | Reasoning-as-a-Skill |

---

## 📄 License

Apache 2.0

---

*The Code guides. The LLM thinks. Z3 proves. The Knowledge Base knows.*
