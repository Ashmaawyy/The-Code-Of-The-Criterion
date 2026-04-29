# Al-Furqan — Architecture v2.0
## Layered Architecture: Engine ↔ Knowledge — Fully Separated

**Date:** March 20, 2026
**Based on:** Mahmoud's review + team discussion
**Principle:** فصل كامل بين طبقة الحكم (الفرقان) وطبقة المعرفة (Knowledge)

---

## 🏗️ The Big Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  REST API (FastAPI) │ CLI │ Future: Mobile/Edge                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                            │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Intent Router │  │ Auth + Rate  │  │ Audit Logger           │ │
│  │              │  │ Limiting     │  │ (model, response, etc) │ │
│  └──────┬───────┘  └──────────────┘  └────────────────────────┘ │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              EVALUATION PIPELINE                          │   │
│  │                                                           │   │
│  │  Question → [Retrieve Context] → [Guided Chains]          │   │
│  │           → [Gate Scoring] → [Verification] → Verdict     │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│  FURQAN LAYER  │ │ KNOWLEDGE      │ │ STORAGE        │
│  (الفرقان)     │ │ LAYER          │ │ LAYER          │
│                │ │ (المعرفة)      │ │ (التخزين)      │
│  Pure Logic    │ │ Pure Data      │ │ Persistence    │
│  No data deps  │ │ No logic deps  │ │                │
└────────────────┘ └────────────────┘ └────────────────┘
```

---

## 📐 Layer 1: FURQAN (الفرقان) — The Criterion Engine

**Purpose:** الحكم والتقييم. منطق صرف. لا يعرف مصدر البيانات ولا يهتم.
**Dependencies:** لا شيء — يعمل بمفرده.

```
src/al_furqan/engine/
├── __init__.py
├── axioms.py              # The 3 axioms + 2 proofs (immutable)
├── gates/
│   ├── __init__.py
│   ├── base.py            # Abstract Gate interface
│   ├── source_integrity.py    # Gate 1
│   ├── structural_consistency.py  # Gate 2
│   ├── mediation_zeroing.py   # Gate 3
│   └── origin_aware.py       # Gate 4
├── chains/
│   ├── __init__.py
│   ├── definitions.py     # Guided chain questions per gate
│   ├── executor.py        # Chain execution engine
│   └── scorer.py          # Deterministic scoring (code, not LLM)
├── symbolic/
│   ├── __init__.py
│   ├── formal_axioms.py   # Z3 encoded axioms
│   ├── gate_checks.py     # Z3 gate verification
│   ├── predicate_extractor.py  # LLM → predicates
│   └── verifier.py        # Orchestrator
├── pipeline.py            # Scan → Mirror → Verdict → Correct
├── models.py              # Verdict, GateScore, DualPerspective
└── prompts.py             # All prompt templates
```

### Interface Contract:
```python
class FurqanEngine:
    """The Criterion — evaluates anything against axioms and gates."""

    def evaluate(self, question: str, context: str = "") -> Verdict:
        """
        Evaluate a question. Context is OPTIONAL.
        - Without context: uses LLM general knowledge (current behavior)
        - With context: uses provided sources (when KB is connected)
        
        The engine doesn't know WHERE the context came from.
        Could be Islamic KB, medical KB, or anything else.
        """

    def evaluate_dual(self, question: str, context: str = "") -> DualPerspectiveVerdict:
        """Dual-perspective evaluation (system + assumptions)."""

    def evaluate_smart(self, question: str, context: str = "") -> Union[Verdict, InformationalResponse]:
        """Smart routing: informational → direct, evaluative → gates."""
```

### Key Rule:
```
❌ The engine NEVER imports from al_furqan.kb
❌ The engine NEVER imports from al_furqan.store
❌ The engine NEVER accesses a database directly

✅ The engine receives a question + optional context string
✅ The engine returns a Verdict object
✅ The engine is testable with ZERO infrastructure
```

---

## 📚 Layer 2: KNOWLEDGE (المعرفة) — Data & Retrieval

**Purpose:** تخزين واسترجاع المعرفة. بيانات صرفة. لا يعرف شيء عن الـ gates أو الـ axioms.
**Dependencies:** Database only.

```
src/al_furqan/kb/
├── __init__.py
├── embeddings.py          # Embedding model (CamelBERT / ModernBERT)
├── collections/
│   ├── __init__.py
│   ├── quran.py           # Quran collection (6,236 verses)
│   ├── hadith.py          # Hadith collection (38,016+)
│   └── fiqh.py            # Fiqh rules (50 core rules)
├── graph/
│   ├── __init__.py
│   ├── store.py           # Graph DB connection (SurrealDB/Neo4j)
│   ├── schema.py          # Node/Edge definitions
│   └── traversal.py       # Graph traversal queries
├── retriever.py           # Unified retrieval: vector + graph
├── knowledge_linker.py    # Extract reasoning chains from transcripts
├── cross_reference.py     # Source cross-referencing
└── ingestion/
    ├── __init__.py
    ├── ingest_quran.py
    ├── ingest_hadith.py
    └── ingest_fiqh.py
```

### Interface Contract:
```python
class KnowledgeRetriever:
    """Retrieves relevant knowledge. Knows nothing about gates or axioms."""

    def retrieve(self, query: str, config: RetrievalConfig = None) -> KnowledgeContext:
        """
        Returns relevant sources for a query.
        The retriever doesn't know HOW the sources will be used.
        
        Returns KnowledgeContext:
          - quran_verses: list[QuranResult]
          - hadith: list[HadithResult]
          - fiqh_rules: list[FiqhResult]
          - reasoning_chains: list[ScholarChain]
          - formatted_text: str  (ready to inject as context)
        """

    def search(self, query: str, collection: str = "all") -> list[SearchResult]:
        """Direct search across collections."""
```

### Key Rule:
```
❌ The KB NEVER imports from al_furqan.engine
❌ The KB NEVER knows about gates, axioms, or scoring
❌ The KB NEVER makes judgments

✅ The KB receives a query
✅ The KB returns sources with relevance scores
✅ The KB is testable with ZERO engine logic
```

---

## 💾 Layer 3: STORAGE (التخزين) — Persistence & Audit

**Purpose:** حفظ النتائج والتاريخ. لا يعرف شيء عن المنطق أو المعرفة.

```
src/al_furqan/store/
├── __init__.py
├── verdict_store.py       # Store/retrieve verdicts (existing)
├── pattern_store.py       # Store reasoning patterns (Sprint 5)
├── feedback_store.py      # Human feedback storage
└── audit_log.py           # Full audit trail
```

### Key Rule:
```
✅ Receives Verdict objects → persists them
✅ Receives queries → returns past verdicts
✅ No business logic, no evaluation, no retrieval
```

---

## 🔌 Layer 4: ORCHESTRATION (التنسيق) — Connects Everything

**Purpose:** الطبقة الوحيدة اللي بتعرف كل الطبقات وبتربطهم.

```
src/al_furqan/api/
├── __init__.py
├── app.py                 # FastAPI app (existing, updated)
├── orchestrator.py        # NEW: connects engine + KB + store
├── schemas.py             # API request/response schemas
├── routers/
│   ├── evaluate.py        # Evaluation endpoints
│   ├── evaluate_grounded.py  # Grounded evaluation (Sprint 5)
│   ├── verdicts.py        # Verdict CRUD
│   ├── sources.py         # KB search (Sprint 5)
│   ├── stats.py           # Statistics
│   └── criterion.py       # Test endpoint
└── middleware/             # Auth, rate limiting, security (Sprint 2)
```

### The Orchestrator:
```python
class Orchestrator:
    """The ONLY component that knows about all layers."""

    def __init__(self, engine: FurqanEngine, kb: KnowledgeRetriever,
                 store: VerdictStore):
        self.engine = engine
        self.kb = kb
        self.store = store

    def evaluate(self, question: str, use_kb: bool = False) -> Verdict:
        """
        Sprint 2-4: use_kb=False → engine evaluates alone
        Sprint 5:   use_kb=True  → KB provides context → engine evaluates
        """
        context = ""
        if use_kb:
            kb_result = self.kb.retrieve(question)
            context = kb_result.formatted_text

        verdict = self.engine.evaluate(question, context=context)
        
        # Store result
        self.store.store(verdict)
        
        return verdict
```

---

## 🔄 Data Flow

### Sprint 2-4 (Current → Engine Refinement):
```
User Question
    ↓
Orchestrator
    ↓
FurqanEngine.evaluate(question)     ← no context, engine uses LLM only
    ↓
Verdict → VerdictStore
    ↓
API Response
```

### Sprint 5 (Integration):
```
User Question
    ↓
Orchestrator
    ├→ KnowledgeRetriever.retrieve(question)     ← get relevant sources
    │      ↓
    │  KnowledgeContext (ayat, hadith, fiqh, chains)
    │      ↓
    ├→ FurqanEngine.evaluate(question, context)   ← engine + sources
    │      ↓
    │  Verdict (with source_citations)
    │      ↓
    └→ VerdictStore.store(verdict)
           ↓
       API Response
```

---

## 🧪 Testing Strategy (Layer Isolation)

### Engine Tests (no KB, no DB):
```python
def test_gate_1_divine_source():
    engine = FurqanEngine(llm=mock_llm)
    verdict = engine.evaluate("Is Zakat fair?")
    assert verdict.gate_scores[0].result == GateResult.SURVIVE

def test_gate_1_human_theory():
    engine = FurqanEngine(llm=mock_llm)
    verdict = engine.evaluate("Is communism fair?")
    assert verdict.gate_scores[0].result == GateResult.FAIL
```

### KB Tests (no engine, no evaluation):
```python
def test_quran_retrieval():
    kb = KnowledgeRetriever(db=test_db)
    results = kb.retrieve("تحريم الربا")
    assert any("2:275" in r.reference for r in results.quran_verses)

def test_hadith_grading_filter():
    kb = KnowledgeRetriever(db=test_db)
    results = kb.retrieve("الربا", min_grading="sahih")
    assert all(r.grading == "sahih" for r in results.hadith)
```

### Integration Tests (Sprint 5):
```python
def test_grounded_evaluation():
    orchestrator = Orchestrator(engine, kb, store)
    verdict = orchestrator.evaluate("Is Zakat fair?", use_kb=True)
    assert len(verdict.source_citations) > 0
    assert verdict.model_info["provider"] is not None
```

---

## 📦 Dependency Diagram

```
                    ┌──────────┐
                    │  CLIENT   │
                    └─────┬────┘
                          │
                    ┌─────▼────┐
                    │   API    │
                    │ (FastAPI)│
                    └─────┬────┘
                          │
                 ┌────────▼────────┐
                 │  ORCHESTRATOR   │
                 └──┬─────┬─────┬─┘
                    │     │     │
          ┌─────────▼┐ ┌─▼────┐ ┌▼─────────┐
          │  ENGINE  │ │  KB  │ │  STORE   │
          │ (فرقان)  │ │(معرفة)│ │ (تخزين)  │
          └─────┬────┘ └──┬───┘ └────┬─────┘
                │         │          │
          ┌─────▼────┐ ┌──▼───┐ ┌───▼────┐
          │ LLM      │ │ DB   │ │ Files/ │
          │ Provider  │ │Vector│ │ ChromaDB│
          │ (LiteLLM) │ │Graph │ │        │
          └──────────┘ └──────┘ └────────┘

  RULE: Arrows only go DOWN. No layer imports from above.
  RULE: Engine ←✗→ KB  (never import each other)
  RULE: Only Orchestrator knows about all layers.
```

---

## 📋 MVP Sprint Plan (Eid Holiday Target 🎯)

### Sprint 3: Knowledge Infrastructure
- [ ] Restructure code to match this architecture
- [ ] Move engine code to `src/al_furqan/engine/`
- [ ] Move KB code to `src/al_furqan/kb/`
- [ ] Create Orchestrator
- [ ] Build KB collections (Quran, Hadith, Fiqh)
- [ ] Model metadata tracking
- [ ] Tests for each layer independently

### Sprint 4: Engine Refinement
- [ ] Symbolic gates (Z3) in `engine/symbolic/`
- [ ] Guided chains in `engine/chains/`
- [ ] Deterministic scoring
- [ ] Human feedback loop
- [ ] 18 edge cases re-tested

### Sprint 5: Integration
- [ ] Orchestrator connects KB → Engine
- [ ] Source citations in verdicts
- [ ] Pattern learning
- [ ] Comparative testing
- [ ] Final documentation

---

## 🔮 Future (Post-MVP)

- **Edge/Mobile:** SurrealDB embedded + verdict cache (Sprint 6+)
- **Multi-domain:** Same engine, different KBs (medical, legal, etc.)
- **Fine-tuning:** After sufficient data, train model on our dataset
- **Rust rewrite:** Performance-critical paths (per QLP v3.0 vision)

---

_Architecture v2.0 — March 20, 2026_
_"The engine judges. The knowledge informs. Neither depends on the other."_
