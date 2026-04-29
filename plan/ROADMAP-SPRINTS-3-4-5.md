# Al-Furqan — Sprints 3, 4, 5 Roadmap
## The Criterion — From Infrastructure to Intelligence

**Version:** 2.0
**Date:** March 20, 2026
**Prepared by:** Arif AI (عارف)
**Contributors:** Muhammad Al-Ashmawy (micro-steps, symbolic AI, knowledge linking), آية أبوالوفا (gate decomposition, Knowledge Graph/Neo4j), Mustafa Marzouk (Symbolic AI research, DSPy analysis, GraphRAG)
**Approach:** Build → Refine → Integrate

---

## 🗺️ High-Level Roadmap

```
Sprint 3: INFRASTRUCTURE          Sprint 4: ENGINE              Sprint 5: INTEGRATION
(Build the foundations)            (Refine the brain)            (Connect everything)

┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
│ Quran DB (6,236)     │   │ Symbolic Gates (Z3)  │   │ Engine ←→ KB         │
│ Hadith DB (38,016)   │   │ Guided Chains        │   │ Source Citations      │
│ Fiqh Rules (50)      │   │ Code Scoring         │   │ Pattern Learning      │
│ Neo4j Graph          │   │ Human Feedback Loop  │   │ Graph-Grounded Gates  │
│ CamelBERT Embeddings │   │ Edge Case Tuning     │   │ Comparative Testing   │
│ Knowledge Linker     │   │ DSPy (extraction)    │   │ API Endpoints         │
│ Model Metadata       │   │                      │   │                       │
└──────────────────────┘   └──────────────────────┘   └──────────────────────┘
     ~4-5 weeks                  ~3-4 weeks                 ~3-4 weeks
     
     NO engine changes           NO KB connection            FULL integration
     Data only                   Engine only                 Everything together
```

---

# Sprint 3: Infrastructure (الأساسات)
## Goal: Build the Knowledge Base and data layer — NO engine changes

**Duration:** 4-5 weeks
**Principle:** مجرد بناء ومليان data. الـ engine مبيتغيّرش.

---

### Phase 3A: Model Metadata Tracking (Week 1, Days 1-2)
**Priority: 🔴 Critical — fixes a gap in current system**

**Problem:** Verdicts don't track which model produced them. Can't compare results across models.

**Deliverables:**
- Extend `Verdict` dataclass with: `model_provider`, `model_name`, `model_temperature`
- Store `raw_scan_response`, `raw_mirror_response`, `raw_verdict_response` for audit
- Update `VerdictStore` serialization (backward compatible)
- Update API response schema with `model_info`

**Files:**
- Modify: `src/al_furqan/core/reasoning_engine.py` (Verdict dataclass)
- Modify: `src/al_furqan/store/verdict_store.py` (serialization)
- Modify: `src/al_furqan/api/schemas.py` (response schema)
- Create: `tests/test_verdict_metadata.py`

**Definition of Done:**
- [ ] Every new verdict stores model info + raw responses
- [ ] Old verdicts still load correctly
- [ ] API response includes `model_info`
- [ ] Tests pass

**Effort:** ~5 hours

---

### Phase 3B: CamelBERT Embedding Setup (Week 1, Days 3-5)

**Problem:** Current multilingual model isn't optimized for Classical Arabic.

**Deliverables:**
- `src/al_furqan/kb/embeddings.py` — CamelBERT wrapper with fallback
- Benchmark: CamelBERT vs multilingual on 20 Islamic queries
- Configuration in `config.yaml`

```python
class ShariaEmbeddingModel:
    PRIMARY = "CAMeL-Lab/bert-base-arabic-camelbert-ca"    # Classical Arabic
    FALLBACK = "paraphrase-multilingual-MiniLM-L12-v2"     # Current model
```

**Definition of Done:**
- [ ] CamelBERT working with CPU fallback
- [ ] Benchmark results documented
- [ ] Embedding config in config.yaml

**Effort:** ~4 hours

---

### Phase 3C: Knowledge Base Collections (Week 2-3)

**Deliverables:**

**3C.1: Quran Collection**
- `src/al_furqan/kb/quran.py` — QuranCollection class
- 6,236 verses with: Arabic text, English translation, Jalalayn, Muyassar tafsir
- Searchable by semantic similarity + surah/ayah reference
- Topic tagging (auto-generated)

**3C.2: Hadith Collection**
- `src/al_furqan/kb/hadith.py` — HadithCollection class
- 38,016+ hadith with grading filter (Sahih/Hasan only as evidence)
- Bilingual (Arabic + English)
- Cross-references between related hadith

**3C.3: Fiqh Rules Collection**
- `src/al_furqan/kb/fiqh.py` — FiqhRulesCollection class
- 50 core rules (القواعد الفقهية الكبرى) — manually curated
- Each rule: Arabic + English + Quran evidence + Hadith evidence + applications
- Gate mapping (which rule relates to which gate)

**3C.4: Ingestion Pipelines**
- `src/al_furqan/kb/ingestion/ingest_quran.py` — from Tanzil data
- `src/al_furqan/kb/ingestion/ingest_hadith.py` — from HuggingFace datasets
- `src/al_furqan/kb/ingestion/ingest_fiqh.py` — from curated JSON
- Validation: verify all data integrity after ingestion

**3C.5: Unified Retriever**
- `src/al_furqan/kb/retriever.py` — ShariaRetriever class
- Semantic search across all collections
- Configurable: how many results per collection
- Returns `ShariaContext` object (formatted, ready for future prompt injection)
- **Does NOT connect to the engine yet** — just retrieval logic

**Files to create:**
```
src/al_furqan/kb/
├── __init__.py
├── embeddings.py
├── quran.py
├── hadith.py
├── fiqh.py
├── retriever.py
├── ingestion/
│   ├── __init__.py
│   ├── ingest_quran.py
│   ├── ingest_hadith.py
│   └── ingest_fiqh.py
└── data/
    └── fiqh_rules_core_50.json
```

**Definition of Done:**
- [ ] All 3 collections populated and searchable
- [ ] Retriever returns relevant results for test queries
- [ ] Grading filter working (only Sahih/Hasan)
- [ ] Fiqh rules manually curated (needs domain expert review)
- [ ] Tests for retrieval accuracy

**Effort:** ~20 hours

---

### Phase 3D: Neo4j Knowledge Graph (Week 3-4)

**Why Neo4j, not just vectors:**
- Vectors say "these are similar" — the graph says **WHY** they're related
- Enables traversal: "from this ayah → find all related hadith → find all scholar explanations"
- Pre-maps sources to gates (which source is relevant to which gate)
- آية's proposal: explicit relationships > implicit similarity

**Deliverables:**

**3D.1: Neo4j Setup & Schema**
```
Node Types:
  (:Ayah {surah, ayah, text_ar, text_en, topics[]})
  (:Hadith {collection, number, text_ar, text_en, grading, narrator})
  (:FiqhRule {text_ar, text_en, category})
  (:Scholar {name})
  (:Lesson {title, scholar, episode, duration})
  (:Gate {name, description})
  (:Maqsad {name_ar, name_en})
  (:Topic {name_ar, name_en})

Relationship Types:
  -[:INTERPRETED_BY]->      (Ayah → Hadith: hadith explains the verse)
  -[:EXPLAINED_BY]->        (Ayah/Hadith → ScholarExplanation)
  -[:ESTABLISHES]->         (Source → FiqhRule)
  -[:MAPS_TO_GATE]->        (Source → Gate: pre-mapped relevance)
  -[:SERVES_MAQSAD]->       (Source → Maqsad)
  -[:RELATES_TO]->           (Ayah ↔ Ayah, Hadith ↔ Hadith)
  -[:TAGGED_WITH]->          (Any → Topic)
  -[:CITED_IN]->             (Source → Lesson)
```

**3D.2: Graph Population**
- Auto-populate from existing ChromaDB data
- Cross-reference Quran ↔ Hadith based on topic overlap
- Map fiqh rules to their source evidence

**3D.3: Graph Retriever**
- `src/al_furqan/kb/graph_retriever.py`
- Given an entry point (from ChromaDB semantic search), traverse the graph
- Return full reasoning chains: ayah + related hadith + scholar explanation + fiqh rule

**Files:**
- Create: `src/al_furqan/kb/graph_store.py` (Neo4j connection + CRUD)
- Create: `src/al_furqan/kb/graph_retriever.py` (traversal queries)
- Create: `src/al_furqan/kb/graph_schema.py` (schema definitions)
- Create: `scripts/populate_neo4j.py` (initial population)
- Create: `tests/test_graph_store.py`

**Definition of Done:**
- [ ] Neo4j running with schema defined
- [ ] All Quran verses, hadith, and fiqh rules as nodes
- [ ] Cross-references as relationships
- [ ] Graph traversal returns connected reasoning chains
- [ ] Tests pass

**Effort:** ~15 hours

---

### Phase 3E: Knowledge Linker — Scholarly Reasoning Chains (Week 4-5)

**Origin:** Muhammad Al-Ashmawy's insight — preserve how scholars connect sources.

**Problem:** When Sheikh Ahmad Al-Sayed explains a verse by connecting it to a hadith, that reasoning chain must be preserved — not just as separate vectors, but as a **linked cluster** in both vector space and the knowledge graph.

**Deliverables:**

**3E.1: Transcript Processing Pipeline**
- Take Whisper transcript (already built in Sprint 1)
- LLM extracts: which ayat? which ahadith? what's the connection?
- Verify references against Quran DB and Hadith DB
- Store as `KnowledgeLink` objects

**3E.2: Composite Embedding**
- Embed ayah + hadith + scholar reasoning as nearby vectors
- Strategy: composite document embedding (ayah text + hadith text + reasoning)

**3E.3: Graph Integration**
- Add `(:ScholarExplanation)` nodes in Neo4j
- Link to `(:Ayah)` and `(:Hadith)` nodes with typed relationships
- Traversal: "from this ayah → find all scholarly explanations → find all connected hadith"

**3E.4: Process Remaining Lessons**
- Transcribe remaining 19 episodes (Whisper pipeline ready)
- Extract reasoning chains from all 20 episodes
- Human review of extracted links (quality check)

**Files:**
- Create: `src/al_furqan/kb/knowledge_linker.py`
- Create: `src/al_furqan/kb/transcript_processor.py`
- Create: `tests/test_knowledge_linker.py`
- Create: `scripts/process_transcripts.py`

**Definition of Done:**
- [ ] Reasoning chains extracted from Episode 1 (POC)
- [ ] Chains stored as linked vectors + Neo4j relationships
- [ ] Retrieval returns full chains (ayah + hadith + scholar reasoning)
- [ ] Pipeline ready for remaining 19 episodes
- [ ] Human review process defined

**Effort:** ~15 hours

---

### Sprint 3 — Summary

| Phase | Focus | Effort | Key Output |
|-------|-------|--------|------------|
| 3A | Model Metadata | ~5h | Every verdict tracks its model |
| 3B | CamelBERT | ~4h | Optimized Arabic embeddings |
| 3C | KB Collections | ~20h | 44,252+ documents searchable |
| 3D | Neo4j Graph | ~15h | Knowledge Graph with explicit relationships |
| 3E | Knowledge Linker | ~15h | Scholarly reasoning chains preserved |
| **Total** | | **~59h** | **Complete data infrastructure** |

**What Sprint 3 does NOT do:**
- ❌ Change the reasoning engine
- ❌ Connect KB to evaluation pipeline
- ❌ Add symbolic gates or Z3
- ❌ Modify scoring logic

---

# Sprint 4: Engine Refinement (تظبيط المحرك)
## Goal: Upgrade the reasoning engine — NO KB connection

**Duration:** 3-4 weeks
**Principle:** الـ engine لوحده بيتحسّن. مفيش ربط بالـ Knowledge Base.

---

### Phase 4A: Symbolic Gates — Z3 Verification (Week 1-2)
**Origin:** Muhammad Al-Ashmawy's Symbolic AI proposal + مصطفى's research paper

**Deliverables:**

**4A.1: Formal Axiom Encoding**
```python
# src/al_furqan/symbolic/axioms.py
# The 3 axioms + 2 proofs encoded as Z3 constraints
# IMMUTABLE — the mathematical foundation

from z3 import *

Entity = DeclareSort('Entity')
Framework = DeclareSort('Framework')

# Transcendence Necessity: Exists(x) → HasPurpose(x)
# Final Court: MoralDebt(d) ∧ ¬HumanJustice(d) → NeedsFinalCourt(d)
```

**4A.2: Gate Z3 Checks**
```python
# src/al_furqan/symbolic/gates.py
# Each gate = Z3 satisfiability check
# LLM extracts predicates → Z3 proves/disproves

def check_gate_1_source_integrity(predicates: dict) -> dict:
    s = Solver()
    # ... encode predicates as Z3 constraints ...
    result = s.check()
    return {"result": "Survive" if result == unsat else "Fail", "proof": ...}
```

**4A.3: Predicate Extractor**
```python
# src/al_furqan/symbolic/predicate_extractor.py
# LLM extracts true/false predicates from question
# These feed into Z3 — the ONLY role of the LLM in judgment

class PredicateExtractor:
    def extract(self, question: str) -> dict:
        # Returns: {
        #   "preserves_truth": true/false,
        #   "has_transcendent_source": true/false,
        #   "relies_on_human_pref": true/false,
        #   "source_type": "divine_text|prophetic|human_theory|...",
        #   ...
        # }
```

**Files:**
```
src/al_furqan/symbolic/
├── __init__.py
├── axioms.py              # Formal axiom encoding (Z3)
├── gates.py               # Gate verification checks
├── predicate_extractor.py # LLM → predicates
└── verifier.py            # Orchestrator: extract → verify → result
```

**Definition of Done:**
- [ ] All 4 gates encoded as Z3 constraints
- [ ] Predicate extractor working (LLM → structured predicates)
- [ ] Z3 verification produces provable results
- [ ] Same predicates → same result regardless of model
- [ ] Tests for all symbolic components

**Effort:** ~20 hours

---

### Phase 4B: Guided Reasoning Chains (Week 2-3)
**Origin:** Muhammad Al-Ashmawy's "سلسلة أسئلة توجيهية" + آية's micro-step decomposition

**Deliverables:**

**4B.1: Chain Definitions**
```python
# src/al_furqan/chains/gate_chains.py

# Each gate has a chain of guided questions
# Each question builds on the previous answer
# The LLM follows the chain, the CODE scores the answers

GATE_1_CHAIN = [
    {"id": "claim", "question": "What is the core claim of this system?", "output": "text"},
    {"id": "source", "question": "What is this claim based on?", "output": "category", 
     "options": ["divine_text", "prophetic", "scholarly_consensus", "human_theory", "empirical", "none"]},
    {"id": "verifiable", "question": "Is the source verifiable?", "output": "bool"},
    {"id": "chain_intact", "question": "Is the chain from claim to source unbroken?", "output": "bool"},
    {"id": "contradictions", "question": "Are there contradictions between the claim and its source?", "output": "list"},
]
```

**4B.2: Chain Executor**
```python
# src/al_furqan/chains/executor.py

class ChainExecutor:
    """Execute a guided reasoning chain step by step."""
    
    def execute(self, chain: list, question: str, context: str = "") -> ChainResult:
        """
        Each step:
        1. Format the question with previous answers as context
        2. LLM answers (structured output)
        3. Validate answer format
        4. Pass to next step
        """
```

**4B.3: Deterministic Scoring**
```python
# src/al_furqan/chains/scorer.py

class DeterministicScorer:
    """Compute gate scores from chain answers — NO LLM involvement."""
    
    def score_gate_1(self, chain_result: ChainResult) -> int:
        base = SOURCE_TYPE_SCORES[chain_result["source"]]  # divine=95, human=40
        verified = 1.0 if chain_result["verifiable"] else 0.5
        chain_penalty = 0.7 if not chain_result["chain_intact"] else 1.0
        contradiction_penalty = len(chain_result["contradictions"]) * 15
        return clamp(base * verified * chain_penalty - contradiction_penalty, 0, 100)
```

**4B.4: DSPy Integration (Optional — for extraction layer only)**
```python
# src/al_furqan/chains/dspy_extractor.py (optional)

class ChainStep(dspy.Signature):
    """Single step in a guided reasoning chain."""
    question: str = dspy.InputField()
    context: str = dspy.InputField()
    answer: str = dspy.OutputField()
```

**Files:**
```
src/al_furqan/chains/
├── __init__.py
├── gate_chains.py      # Chain definitions per gate
├── executor.py         # Chain execution engine
├── scorer.py           # Deterministic scoring
└── dspy_extractor.py   # Optional DSPy integration
```

**Definition of Done:**
- [ ] All 4 gates have guided chains defined
- [ ] Chain executor produces structured outputs
- [ ] Scoring is 100% deterministic (same inputs → same score)
- [ ] Scoring functions have 100% test coverage

**Effort:** ~15 hours

---

### Phase 4C: Human Feedback Loop (Week 3-4)

**Deliverables:**

**4C.1: Enhanced Human Review**
- Update `human_review.py` to show chain reasoning steps
- Reviewer can approve/reject **per gate** (not just whole verdict)
- Reviewer can correct specific predicate extractions
- Feedback stored with the verdict for learning

**4C.2: Feedback-Driven Improvement**
- Collect human corrections → identify patterns
- "Gate 1 keeps extracting 'human_theory' when it should be 'scholarly_consensus'" → adjust chain prompts
- Track accuracy metrics per gate over time

**4C.3: Edge Case Re-Testing**
- Re-run all 18 edge cases with new symbolic gates + guided chains
- Compare: old engine vs new engine (without KB)
- Document improvements and remaining failures
- Use failures to refine chains and scoring weights

**Definition of Done:**
- [ ] Human review shows full chain reasoning
- [ ] Per-gate approval working
- [ ] Feedback stored and queryable
- [ ] 18 edge cases re-tested and documented
- [ ] Accuracy improved from 83% to target ≥88%

**Effort:** ~15 hours

---

### Sprint 4 — Summary

| Phase | Focus | Effort | Key Output |
|-------|-------|--------|------------|
| 4A | Symbolic Gates (Z3) | ~20h | Formal verification layer |
| 4B | Guided Chains | ~15h | Deterministic scoring |
| 4C | Human Feedback | ~15h | Self-improving accuracy |
| **Total** | | **~50h** | **Refined engine, no KB dependency** |

**What Sprint 4 does NOT do:**
- ❌ Connect to Knowledge Base
- ❌ Add source citations to verdicts
- ❌ Use Neo4j graph in evaluation
- ❌ Pattern learning from past verdicts

---

# Sprint 5: Integration (الربط)
## Goal: Connect the refined engine to the Knowledge Base

**Duration:** 3-4 weeks
**Principle:** ربط كل حاجة ببعض. الـ engine يقرأ من الـ KB.

---

### Phase 5A: Source-Grounded Evaluation (Week 1-2)

**Deliverables:**

**5A.1: KB → Engine Pipeline**
```python
# Updated evaluation pipeline:
def evaluate_grounded(self, question: str) -> Verdict:
    # Phase 0: Intent detection (existing)
    intent = self.detect_intent(question)
    
    # Phase 0.5: Sharia RAG retrieval (NEW — from Sprint 3)
    sharia_context = self.retriever.retrieve(question)
    graph_context = self.graph_retriever.expand(sharia_context)
    
    # Phase 1-4: Guided chains WITH sources (NEW — from Sprint 4 + 3)
    chain_results = self.chain_executor.execute_with_sources(
        question, graph_context
    )
    
    # Phase 5: Z3 verification WITH source evidence
    verdict = self.verifier.verify(chain_results, sharia_context)
    
    return verdict
```

**5A.2: Source Citations in Verdicts**
- Every gate reasoning includes specific citations
- Citations validated against KB (no hallucinations)
- Format: `[Quran 2:275]`, `[Bukhari:1395]`, `[Fiqh: الضرر يزال]`

**5A.3: Graph-Grounded Gates**
- The guided chain questions now include relevant sources from Neo4j
- "Given these Quran verses and hadith, is the source verifiable?"
- The graph pre-maps which sources are relevant to which gate

---

### Phase 5B: Pattern Learning (Week 2-3)

**Deliverables:**
- `PatternStore`: store successful reasoning chains
- Pattern matching: find similar past evaluations
- Confidence scoring: patterns that were human-approved get higher confidence
- Context injection: similar patterns pre-load into the chain

---

### Phase 5C: API & Comparative Testing (Week 3-4)

**Deliverables:**
- New endpoint: `POST /api/v1/evaluate-grounded`
- New endpoint: `GET /api/v1/sources/search`
- New endpoint: `GET /api/v1/patterns`
- Re-run 18 edge cases: **ungrounded vs grounded vs grounded+symbolic**
- Cross-model consistency test: same question, 3 different models
- Final documentation and comparative report

---

### Sprint 5 — Summary

| Phase | Focus | Effort | Key Output |
|-------|-------|--------|------------|
| 5A | Source-Grounded Evaluation | ~20h | KB integrated with engine |
| 5B | Pattern Learning | ~15h | Self-improving from experience |
| 5C | API & Testing | ~15h | New endpoints + comparative report |
| **Total** | | **~50h** | **Fully integrated system** |

---

## 📊 Success Metrics (Across All 3 Sprints)

| Metric | After Sprint 2 | After Sprint 3 | After Sprint 4 | After Sprint 5 |
|--------|----------------|----------------|----------------|----------------|
| Source citation rate | 0% | N/A (no engine) | 0% (no KB) | **≥95%** |
| Cross-model consistency | ~70% | N/A | **≥85%** | **≥90%** |
| Edge case accuracy | 83% | N/A | **≥88%** | **≥93%** |
| Model tracking | ❌ | ✅ | ✅ | ✅ |
| Formal proofs | ❌ | ❌ | ✅ (Z3) | ✅ (Z3 + sources) |
| Knowledge Graph | ❌ | ✅ (built) | ❌ (not used) | ✅ (integrated) |
| Reasoning audit trail | ❌ | ❌ | ✅ (chains) | ✅ (chains + citations) |
| Human feedback loop | ❌ | ❌ | ✅ | ✅ |

---

## 🔧 Tech Stack (Final Architecture)

```
┌─────────────────────────────────────────────────────────┐
│                     User Question                        │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Intent Detection (Phase 0)                  │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│         Hybrid Retrieval (Phase 0.5)                     │
│  ChromaDB (semantic) → Neo4j (graph traversal)           │
│  CamelBERT embeddings │ Knowledge Linker chains          │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│         Guided Reasoning Chains (Phase 1-3)              │
│  Questions → LLM extracts → Code scores                  │
│  DSPy (optional) │ Structured JSON outputs               │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│         Z3 Symbolic Verification (Phase 4)               │
│  Predicates → Z3 Solver → Proof/Disproof                 │
│  Formal axioms │ Gate constraints                        │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│         Source-Grounded Verdict (Phase 5)                 │
│  Citations │ Derivation method │ Maqasid assessment      │
│  Pattern store │ Human feedback loop                     │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 Research References

| Paper/Project | Relevance | URL |
|--------------|-----------|-----|
| **VERGE** (2026) | LLM + Z3 verification — closest to our approach | arxiv.org/abs/2601.20055 |
| **Nucleoid** | Logic Graph runtime for neuro-symbolic AI | github.com/NucleoidAI/Nucleoid |
| **Synalinks** | Keras-like framework for neuro-symbolic LM | github.com/SynaLinks/synalinks |
| **ABLkit** | Abductive Learning (ML + logical reasoning) | github.com/AbductiveLearning/ABLkit |
| **GraphRAG** (Microsoft) | Knowledge graph + RAG approach | microsoft.github.io/graphrag |
| **Neuro-Symbolic AI Survey** (2025) | Comprehensive review, 84 citations | arxiv.org/abs/2501.05435 |
| **DSPy** (Stanford) | Declarative LM programming framework | dspy.ai |
| **Symbolic AI** (Wikipedia) | Foundation — مصطفى's original reference | en.wikipedia.org/wiki/Symbolic_artificial_intelligence |

---

## ⚠️ Dependencies & Risks

| Dependency | Sprint | Risk | Mitigation |
|-----------|--------|------|------------|
| CamelBERT download (~440MB) | 3 | Low | CPU fallback available |
| Neo4j setup | 3 | Low | Docker image available |
| Fiqh rules curation (50) | 3 | Medium | Needs domain expert |
| Z3 Python bindings | 4 | Low | pip install z3-solver |
| Human reviewers for feedback | 4 | Medium | Team can review |
| LLM extraction quality | 4 | Medium | Guided chains reduce ambiguity |
| Integration complexity | 5 | High | Modular design, each layer testable independently |

---

_Roadmap v2.0 — March 20, 2026_
_Project: Al-Furqan — The Criterion_
_Sprints 3-5: Infrastructure → Engine → Integration_
_Contributors: عارف، محمد عشماوي، آية أبوالوفا، مصطفى مرزوق_
