# Sprint 3: Knowledge Base Integration & Source-Grounded Evaluation
## Al-Furqan — The Criterion
### Complete Implementation Plan

**Version:** 1.0
**Date:** March 20, 2026
**Estimated Duration:** 5-7 weeks (5 sub-sprints)
**Prepared by:** Arif AI (عارف)
**Based on:** PRD-ADDENDUM-SHARIA-KB-v1.0.md + آية's micro-step decomposition proposal

---

## 🎯 Sprint Goal

Transform the Al-Furqan engine from an **LLM-opinion-based reasoner** into a **source-grounded Islamic reasoning system** where:
1. Every verdict cites specific Quran/Hadith/Fiqh sources
2. Gate scoring is **extracted by the LLM, computed by code** (not LLM-scored)
3. Results are **consistent across different LLM providers**
4. The system **accumulates intelligence** through pattern learning

---

## 🏗️ Architecture: Before vs After

### Before (Current — Sprint 2)
```
Question → LLM "evaluate this" → LLM picks a score → Verdict
                                  (model-dependent!)
```

### After (Sprint 3)
```
Question
  ↓
Intent Detection (Phase 0)
  ↓
Sharia RAG Retrieval (Phase 0.5) — finds relevant sources
  ↓
Micro-Step Gate Extraction (Phase 1-3) — LLM extracts facts, CODE scores
  ↓
Source-Grounded Verdict (Phase 4) — every claim has a citation
  ↓
Pattern Store (Phase 5) — learns from successful evaluations
```

---

## 📋 Sub-Sprint Breakdown

---

### Sprint 3A: Metadata & Model Tracking (Week 1, Days 1-2)
**Priority: 🔴 Critical — fixes a gap identified by the team**

#### Problem
The current `Verdict` dataclass doesn't track which LLM model produced it, what raw response was returned, or what sources were used. This makes it impossible to compare results across models or audit reasoning.

#### Implementation

**3A.1: Extend Verdict Dataclass**
```python
# src/al_furqan/core/reasoning_engine.py — Verdict additions

@dataclass
class Verdict:
    # ... existing fields ...

    # NEW: Model tracking
    model_provider: str = ""        # "anthropic", "dashscope", "ollama"
    model_name: str = ""            # "claude-haiku-4-5", "qwen3-235b-a22b"
    model_temperature: float = 0.0  # temperature used

    # NEW: Source citations
    source_citations: list[dict] = field(default_factory=list)
    # Each citation: {
    #   "type": "quran|hadith|fiqh|pattern",
    #   "reference": "Al-Ma'idah 5:90",
    #   "text_ar": "...",
    #   "text_en": "...",
    #   "relevance_score": 0.95,
    #   "used_in_gate": "source_integrity",
    #   "grading": "sahih"  # hadith only
    # }

    # NEW: Raw responses (for audit/debugging)
    raw_scan_response: str = ""
    raw_mirror_response: str = ""
    raw_verdict_response: str = ""

    # NEW: Derivation tracking
    derivation_method: str = ""      # "نص صريح", "قياس", etc.
    derivation_confidence: float = 0.0
    maqasid_impact: dict = field(default_factory=dict)
```

**3A.2: Update ReasoningEngine to Pass Model Info**
```python
# The engine's evaluate() method must capture and store model info
def evaluate(self, question: str) -> Verdict:
    # ... existing pipeline ...
    verdict.model_provider = self.llm_config.provider
    verdict.model_name = self.llm_config.model_name
    verdict.model_temperature = self.llm_config.temperature
    verdict.raw_scan_response = scan_raw
    verdict.raw_mirror_response = mirror_raw
    verdict.raw_verdict_response = verdict_raw
    return verdict
```

**3A.3: Update VerdictStore Serialization**
- Update `to_dict()` / `from_dict()` to include new fields
- Update JSON file schema
- Backward-compatible: old verdicts load fine (defaults for new fields)

**3A.4: Update API Response Schema**
```python
# src/al_furqan/api/schemas.py — add model_info to response
class VerdictResponse(BaseModel):
    # ... existing fields ...
    model_info: dict = {}      # {"provider": "...", "model": "...", "temperature": 0.1}
    source_citations: list = []
```

**Files to create/modify:**
- Modify: `src/al_furqan/core/reasoning_engine.py` (Verdict dataclass)
- Modify: `src/al_furqan/store/verdict_store.py` (serialization)
- Modify: `src/al_furqan/api/schemas.py` (response schema)
- Modify: `src/al_furqan/api/routers/evaluate.py` (pass model info)
- Create: `tests/test_verdict_metadata.py`

**Definition of Done:**
- [ ] Every new verdict stores model_provider, model_name, model_temperature
- [ ] Raw LLM responses stored for audit
- [ ] API response includes model_info
- [ ] Old verdicts still load correctly (backward compatible)
- [ ] Tests pass

**Estimated effort:** 4-5 hours

---

### Sprint 3B: Knowledge Base Core (Week 1-2)
**Priority: 🔴 Critical — foundational for all other sub-sprints**

#### 3B.1: CamelBERT Embedding Setup

**Problem:** Current embedding model (`paraphrase-multilingual-MiniLM-L12-v2`) is trained on modern text. Classical Arabic has different vocabulary and structure.

**Solution:**
```python
# src/al_furqan/kb/embeddings.py

class ShariaEmbeddingModel:
    """Embedding model optimized for Classical Arabic text."""

    PRIMARY_MODEL = "CAMeL-Lab/bert-base-arabic-camelbert-ca"  # Classical Arabic
    FALLBACK_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self, model_name: str = None):
        self.model_name = model_name or self.PRIMARY_MODEL
        try:
            self.model = SentenceTransformer(self.model_name)
        except Exception:
            logger.warning("CamelBERT not available, falling back to multilingual model")
            self.model = SentenceTransformer(self.FALLBACK_MODEL)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts."""
        return self.model.encode(texts).tolist()
```

**Benchmark test:**
```python
# Test to verify CamelBERT outperforms multilingual on Classical Arabic
queries = [
    "تحريم الربا",  # prohibition of usury
    "إنما الأعمال بالنيات",  # actions by intentions
    "حد السرقة",  # punishment for theft
]
# Compare retrieval accuracy between models
```

#### 3B.2: Knowledge Base Architecture

```
src/al_furqan/kb/
├── __init__.py
├── embeddings.py         # CamelBERT embedding model
├── base.py               # Abstract KnowledgeCollection class
├── quran.py              # QuranCollection — 6,236 verses
├── hadith.py             # HadithCollection — 38,016+ hadith
├── fiqh.py               # FiqhRulesCollection — 50 curated rules
├── retriever.py          # ShariaRetriever — unified retrieval across all collections
├── cross_reference.py    # Cross-reference expansion engine
├── ingestion/
│   ├── __init__.py
│   ├── ingest_quran.py   # Quran ingestion pipeline (from Tanzil)
│   ├── ingest_hadith.py  # Hadith ingestion pipeline (from HuggingFace)
│   └── ingest_fiqh.py    # Fiqh rules ingestion (from curated JSON)
└── data/
    └── fiqh_rules_core_50.json  # Manually curated fiqh rules
```

#### 3B.3: Quran Collection

```python
# src/al_furqan/kb/quran.py

class QuranCollection:
    """Vectorized Quran collection with tafsir for semantic retrieval."""

    COLLECTION_NAME = "quran_ayat"

    def __init__(self, chroma_client, embedding_model):
        self.collection = chroma_client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=embedding_model,
        )

    def search(self, query: str, n_results: int = 10) -> list[QuranResult]:
        """Semantic search over Quran verses.

        Returns list of QuranResult with:
        - surah_number, ayah_number
        - text_ar, text_en
        - tafsir_jalalayn, tafsir_muyassar
        - relevance_score
        """

    def get_by_reference(self, ref: str) -> Optional[QuranResult]:
        """Get specific verse by reference (e.g., '5:90')."""

    def get_surah_context(self, surah: int, ayah: int, window: int = 3) -> list[QuranResult]:
        """Get surrounding verses for context."""
```

**Document schema (per ayah):**
```json
{
    "id": "quran_5_90",
    "document": "يا أيها الذين آمنوا إنما الخمر والميسر والأنصاب والأزلام رجس من عمل الشيطان...\nO you who have believed, indeed, intoxicants, gambling...\nTafsir: ...",
    "metadata": {
        "surah_number": 5,
        "surah_name_ar": "المائدة",
        "surah_name_en": "Al-Ma'idah",
        "ayah_number": 90,
        "juz": 7,
        "topics": ["alcohol", "gambling", "prohibition"],
        "has_ruling": true,
        "ruling_type": "prohibition"
    }
}
```

#### 3B.4: Hadith Collection

```python
# src/al_furqan/kb/hadith.py

class HadithCollection:
    """Vectorized Hadith collection with grading and cross-references."""

    COLLECTION_NAME = "hadith_corpus"

    # Only allow these gradings as evidence
    ACCEPTABLE_GRADINGS = {"sahih", "hasan", "صحيح", "حسن"}

    def search(self, query: str, n_results: int = 15,
               min_grading: str = "hasan") -> list[HadithResult]:
        """Search with automatic grading filter."""

    def get_by_reference(self, collection: str, number: int) -> Optional[HadithResult]:
        """Get specific hadith (e.g., 'bukhari', 1)."""

    def get_related(self, hadith_id: str) -> list[HadithResult]:
        """Find related hadith by content similarity."""
```

**Grading filter logic:**
```python
GRADING_HIERARCHY = {
    "sahih": 3, "صحيح": 3,
    "hasan": 2, "حسن": 2,
    "daif": 1, "ضعيف": 1,
    "mawdu": 0, "موضوع": 0,
}

def passes_grading_filter(grading: str, min_grading: str = "hasan") -> bool:
    return GRADING_HIERARCHY.get(grading.lower(), 0) >= GRADING_HIERARCHY.get(min_grading, 2)
```

#### 3B.5: Fiqh Rules Collection

```python
# src/al_furqan/kb/fiqh.py

class FiqhRulesCollection:
    """The 50 core fiqh rules (القواعد الفقهية الكبرى)."""

    def search(self, query: str, n_results: int = 5) -> list[FiqhResult]:
        """Find relevant fiqh rules for a question."""

    def get_by_gate(self, gate_name: str) -> list[FiqhResult]:
        """Get rules mapped to a specific gate."""
```

**Initial 50 rules (to be curated manually):**

The 5 Major Rules (القواعد الخمس الكبرى):
1. الأمور بمقاصدها — Matters are judged by their intentions
2. اليقين لا يزول بالشك — Certainty is not overruled by doubt
3. المشقة تجلب التيسير — Hardship brings ease
4. الضرر يزال — Harm must be eliminated
5. العادة محكّمة — Custom is authoritative

Plus 45 more sub-rules and derivative rules, each with:
- Arabic text + English translation
- Quranic evidence
- Hadith evidence
- Gate mapping
- Application examples

#### 3B.6: Unified Retriever

```python
# src/al_furqan/kb/retriever.py

class ShariaRetriever:
    """Unified retrieval engine across all knowledge collections."""

    def __init__(self, quran: QuranCollection, hadith: HadithCollection,
                 fiqh: FiqhRulesCollection, cross_ref: CrossReferenceEngine):
        self.quran = quran
        self.hadith = hadith
        self.fiqh = fiqh
        self.cross_ref = cross_ref

    def retrieve(self, question: str, config: RetrievalConfig = None) -> ShariaContext:
        """
        Full retrieval pipeline:
        1. Semantic search across all collections
        2. Cross-reference expansion
        3. Relevance scoring & ranking
        4. Deduplication
        5. Format for prompt injection

        Returns ShariaContext with:
        - quran_verses: list[QuranResult]
        - hadith: list[HadithResult]
        - fiqh_rules: list[FiqhResult]
        - cross_references: dict  (which sources reference each other)
        - total_sources: int
        - formatted_prompt_context: str  (ready to inject into LLM prompt)
        """

    def retrieve_for_gate(self, gate_name: str, question: str) -> ShariaContext:
        """Targeted retrieval for a specific gate evaluation."""
```

**RetrievalConfig:**
```python
@dataclass
class RetrievalConfig:
    quran_count: int = 10
    hadith_count: int = 15
    fiqh_count: int = 5
    min_hadith_grading: str = "hasan"
    expand_cross_references: bool = True
    max_total_sources: int = 25  # prevent context overflow
```

#### 3B.7: Cross-Reference Engine

```python
# src/al_furqan/kb/cross_reference.py

class CrossReferenceEngine:
    """
    Expand retrieved sources by following cross-references.

    If we find Quran 5:90 (alcohol prohibition), automatically pull:
    - Related hadith about alcohol
    - Related fiqh rules about prohibition
    - Other Quran verses in the same topic cluster
    """

    def expand(self, sources: list[SourceResult]) -> list[SourceResult]:
        """Expand source list by following cross-references."""

    def build_citation_graph(self, sources: list[SourceResult]) -> dict:
        """Build a graph of which sources reference each other."""
```

**Files to create:**
- `src/al_furqan/kb/__init__.py`
- `src/al_furqan/kb/embeddings.py`
- `src/al_furqan/kb/base.py`
- `src/al_furqan/kb/quran.py`
- `src/al_furqan/kb/hadith.py`
- `src/al_furqan/kb/fiqh.py`
- `src/al_furqan/kb/retriever.py`
- `src/al_furqan/kb/cross_reference.py`
- `src/al_furqan/kb/ingestion/__init__.py`
- `src/al_furqan/kb/ingestion/ingest_quran.py`
- `src/al_furqan/kb/ingestion/ingest_hadith.py`
- `src/al_furqan/kb/ingestion/ingest_fiqh.py`
- `src/al_furqan/kb/data/fiqh_rules_core_50.json`
- `tests/test_kb_quran.py`
- `tests/test_kb_hadith.py`
- `tests/test_kb_retriever.py`

#### 3B.8: Cross-Modal Knowledge Linking (Scholarly Reasoning Chains)

**Origin:** Muhammad Al-Ashmawy's insight — when a scholar (e.g., Sheikh Ahmad Al-Sayed) explains
a verse by connecting it to a hadith and deriving a ruling, that **reasoning chain** must be
preserved as linked vectors in the knowledge base.

**Problem:** Currently, Quran verses, hadith, and lesson transcripts are stored in separate
collections with independent embeddings. When a scholar explains verse X using hadith Y,
there's no record that these two sources are **logically connected through scholarly reasoning**.

**Solution: Linked Knowledge Clusters**

```python
# src/al_furqan/kb/knowledge_linker.py

@dataclass
class KnowledgeLink:
    """A scholarly reasoning chain linking multiple sources."""
    link_id: str
    scholar: str                    # "الشيخ أحمد السيد"
    lesson_reference: str           # "مدارسة الأنعام — الحلقة 01"
    timestamp_range: tuple          # (start_sec, end_sec) in transcript

    # The linked sources
    quran_refs: list[str]           # ["6:102", "6:103"]
    hadith_refs: list[str]          # ["bukhari:7405", "muslim:2677"]
    fiqh_rules: list[str]           # ["الأمور بمقاصدها"]

    # The scholarly reasoning connecting them
    reasoning_text: str             # The scholar's explanation
    reasoning_type: str             # "tafsir" | "istidlal" | "ta'lil" | "istinbat"
    topic_tags: list[str]           # ["توحيد", "أسماء الله"]

class KnowledgeLinker:
    """
    Extract and store scholarly reasoning chains from lesson transcripts.

    Pipeline:
    1. Take a lesson transcript segment
    2. LLM extracts: which ayat? which ahadith? what's the connection?
    3. Fetch actual texts from Quran DB and Hadith DB
    4. Create a KnowledgeLink with the scholar's reasoning
    5. Embed ALL linked items (ayah + hadith + reasoning) in nearby vector space
    """

    def extract_links_from_transcript(self, transcript_segment: str,
                                       scholar: str) -> list[KnowledgeLink]:
        """
        Use LLM to identify Quran/Hadith references in scholar's speech,
        then verify and link them.
        """

    def embed_linked_cluster(self, link: KnowledgeLink) -> None:
        """
        Embed the ayah, hadith, and scholar reasoning as a CLUSTER
        in vector space — ensuring they're close to each other.

        Strategy:
        - Create a composite document: ayah_text + hadith_text + reasoning
        - Embed with shared context so vectors are naturally close
        - Store cross-reference metadata for retrieval
        """

    def retrieve_reasoning_chain(self, query: str) -> list[KnowledgeLink]:
        """
        When a question matches a linked cluster, return the FULL chain:
        ayah + hadith + scholar's reasoning — not just individual sources.
        """
```

**Why this matters for the engine:**
- Without linking: "What does Islam say about X?" → isolated ayah + isolated hadith
- With linking: "What does Islam say about X?" → ayah + hadith + **scholar's reasoning connecting them** → the engine understands WHY these sources go together

**Embedding strategy for proximity:**
```python
# Option A: Composite embedding (simple, effective)
composite_text = f"""
[آية] {ayah_text}
[حديث] {hadith_text}
[شرح] {scholar_reasoning}
[الربط] {connection_explanation}
"""
# Single embedding captures the relationship

# Option B: Shared-context multi-embedding (more granular)
# Embed each source WITH the context of the others
ayah_embedding = embed(f"{ayah_text} | Context: {hadith_text} {reasoning}")
hadith_embedding = embed(f"{hadith_text} | Context: {ayah_text} {reasoning}")
# These will naturally cluster in vector space
```

**Integration with Whisper pipeline:**
The lesson transcription pipeline (already built in Sprint 1 — 53 min Sheikh Ahmad Al-Sayed)
becomes the INPUT for the Knowledge Linker. The 19 remaining episodes are a goldmine
of scholarly reasoning chains waiting to be extracted and linked.

**Definition of Done:**
- [ ] CamelBERT embedding working (with multilingual fallback)
- [ ] Quran collection: 6,236 verses searchable
- [ ] Hadith collection: 38,016 hadith searchable with grading filter
- [ ] Fiqh rules: 50 rules curated and indexed
- [ ] Cross-reference expansion working
- [ ] **Knowledge Linker: extract reasoning chains from transcripts**
- [ ] **Linked clusters: ayah + hadith + reasoning embedded as nearby vectors**
- [ ] Unified retriever returns formatted context (including linked chains)
- [ ] Retrieval accuracy benchmarks pass
- [ ] All tests pass

**Estimated effort:** 20-25 hours (increased from 15-20 to include Knowledge Linking)

---

### Sprint 3C: Micro-Step Gate Decomposition (Week 3-4)
**Priority: 🔴 Critical — this is the key architectural change**
**Origin: آية's proposal for deterministic, model-independent evaluation**

#### The Core Problem

Currently, each gate is a single LLM prompt that asks the model to:
1. Understand the concept ← model-dependent
2. Find evidence ← model-dependent
3. Evaluate quality ← model-dependent
4. Pick a score ← model-dependent

**Every step is model-dependent.** That's why Haiku and Qwen3 give different results.

#### The Solution: Extract → Compute

Split each gate into **micro-steps** where:
- The **LLM extracts** (factual, structured, verifiable)
- The **code computes** (deterministic, model-independent)

#### 3C.1: Gate 1 — Source Integrity (المصدر)

**Current (1 prompt, model scores):**
```
"Evaluate the source integrity of this system"
→ LLM returns: { score: 85, reasoning: "..." }
```

**New (4 micro-steps, code scores):**

```python
class SourceIntegrityGate:
    """Gate 1: Does this system trace to a verifiable, authoritative source?"""

    def evaluate(self, question: str, sources: ShariaContext) -> GateScore:

        # Step 1: EXTRACT — What source does this system claim?
        step1 = self.llm_extract(
            prompt="""Given this system/claim, identify:
            1. claimed_source: What authority does it claim? (text, person, institution, revelation)
            2. source_type: "divine_text" | "prophetic" | "scholarly_consensus" | "human_theory" | "empirical" | "none"
            3. specific_references: List exact references if any

            Answer as JSON. Do NOT evaluate — only identify.
            """,
            question=question,
        )  # Returns: {"claimed_source": "...", "source_type": "...", "specific_references": [...]}

        # Step 2: VERIFY — Do our sources confirm this?
        step2 = self.verify_against_kb(
            claimed_references=step1["specific_references"],
            sources=sources,
        )  # Returns: {"verified": 3, "unverified": 1, "contradicted": 0}

        # Step 3: EXTRACT — Is the source chain intact?
        step3 = self.llm_extract(
            prompt="""Given the system's claimed source and these verified references,
            answer ONLY:
            1. chain_intact: true/false — is there an unbroken chain from claim to source?
            2. chain_gaps: list any gaps or missing links
            3. source_accessibility: "public" | "restricted" | "lost" | "mythical"

            DO NOT score. Only describe what you find.
            """,
            verified_sources=step2,
        )

        # Step 4: COMPUTE — Code calculates the score deterministically
        score = self.compute_score(
            source_type=step1["source_type"],
            verified_ratio=step2["verified"] / max(1, step2["verified"] + step2["unverified"]),
            chain_intact=step3["chain_intact"],
            source_accessibility=step3["source_accessibility"],
        )  # Deterministic! Same inputs → same score regardless of model

        return GateScore(
            name="Source-Integrity",
            score=score,
            result=GateResult.SURVIVE if score >= 50 else GateResult.FAIL,
            reasoning=self._format_reasoning(step1, step2, step3),
            extraction_steps=[step1, step2, step3],  # NEW: audit trail
        )

    def compute_score(self, source_type, verified_ratio, chain_intact, source_accessibility):
        """Deterministic scoring — NO LLM involvement."""
        base_scores = {
            "divine_text": 95,
            "prophetic": 85,
            "scholarly_consensus": 75,
            "empirical": 60,
            "human_theory": 40,
            "none": 10,
        }
        score = base_scores.get(source_type, 30)

        # Adjust for verification
        score = score * (0.5 + 0.5 * verified_ratio)  # 50-100% of base based on verification

        # Chain integrity
        if not chain_intact:
            score *= 0.7  # 30% penalty

        # Accessibility
        if source_accessibility == "lost":
            score *= 0.5
        elif source_accessibility == "mythical":
            score *= 0.3

        return min(100, max(0, int(score)))
```

#### 3C.2: Gate 2 — Structural Consistency (البنية)

**Micro-steps:**
```python
class StructuralConsistencyGate:
    """Gate 2: Is the system internally consistent and logically coherent?"""

    def evaluate(self, question: str, sources: ShariaContext) -> GateScore:

        # Step 1: EXTRACT contradictions
        step1 = self.llm_extract("""
            List ALL internal contradictions in this system.
            For each contradiction:
            - claim_a: first claim
            - claim_b: contradicting claim
            - severity: "fatal" | "major" | "minor"
            If no contradictions found, return empty list.
            DO NOT evaluate. Only list contradictions.
        """)

        # Step 2: EXTRACT causal chain
        step2 = self.llm_extract("""
            Map the causal chain of this system:
            - premises: list the starting assumptions
            - derivations: list each logical step (premise → conclusion)
            - gaps: list any logical leaps without justification
            DO NOT score. Only map the logic.
        """)

        # Step 3: VERIFY against Islamic structural principles
        step3 = self.verify_structural_principles(
            causal_chain=step2,
            fiqh_rules=sources.fiqh_rules,
        )

        # Step 4: COMPUTE
        score = self.compute_score(
            contradictions=step1,
            logical_gaps=step2["gaps"],
            structural_alignment=step3,
        )

    def compute_score(self, contradictions, logical_gaps, structural_alignment):
        score = 100
        # Deduct for contradictions
        for c in contradictions:
            if c["severity"] == "fatal": score -= 40
            elif c["severity"] == "major": score -= 20
            elif c["severity"] == "minor": score -= 10
        # Deduct for logical gaps
        score -= len(logical_gaps) * 15
        # Bonus for structural alignment with fiqh
        score += structural_alignment * 10
        return min(100, max(0, score))
```

#### 3C.3: Gate 3 — Mediation Zeroing (الوساطة)

**Micro-steps:**
```python
class MediationZeroingGate:
    """Gate 3: Does this system rely on human preference as its foundation?"""

    def evaluate(self, question: str, sources: ShariaContext) -> GateScore:

        # Step 1: EXTRACT foundation type
        step1 = self.llm_extract("""
            What is the ULTIMATE foundation of this system?
            - foundation_type: "divine_command" | "natural_law" | "social_contract" | "human_preference" | "utilitarian" | "mixed"
            - foundation_evidence: what supports this classification?
            - human_mediators: list any humans whose opinion shapes the foundation
            DO NOT evaluate. Only classify.
        """)

        # Step 2: EXTRACT human preference dependencies
        step2 = self.llm_extract("""
            List every point where this system depends on human preference/opinion:
            - dependency: description
            - removable: true/false (would the system work without this human preference?)
            - alternative: what non-human-preference alternative exists?
            DO NOT evaluate. Only list.
        """)

        # Step 3: COMPUTE — how much human mediation?
        score = self.compute_score(
            foundation_type=step1["foundation_type"],
            mediators=step1["human_mediators"],
            dependencies=step2,
        )

    def compute_score(self, foundation_type, mediators, dependencies):
        foundation_scores = {
            "divine_command": 100,
            "natural_law": 75,
            "mixed": 50,
            "social_contract": 30,
            "utilitarian": 20,
            "human_preference": 10,
        }
        score = foundation_scores.get(foundation_type, 30)

        # Penalize for non-removable human dependencies
        non_removable = sum(1 for d in dependencies if not d.get("removable", True))
        score -= non_removable * 15

        return min(100, max(0, score))
```

#### 3C.4: Gate 4 — Origin Aware (الأصل)

**Micro-steps:**
```python
class OriginAwareGate:
    """Gate 4: Does this system acknowledge a transcendent origin?"""

    def evaluate(self, question: str, sources: ShariaContext) -> GateScore:

        # Step 1: EXTRACT origin claims
        step1 = self.llm_extract("""
            Does this system acknowledge a transcendent (beyond-human) origin?
            - acknowledges_transcendent: true/false
            - transcendent_source: description (if any)
            - origin_type: "divine" | "natural_order" | "human_created" | "emergent" | "denied"
            DO NOT evaluate. Only classify.
        """)

        # Step 2: VERIFY against Quran/Hadith
        step2 = self.verify_origin_against_sources(
            origin_claim=step1,
            quran_verses=sources.quran_verses,
            hadith=sources.hadith,
        )

        # Step 3: COMPUTE
        return GateResult.SURVIVE if step1["acknowledges_transcendent"] and step2["aligned"] else GateResult.FAIL
```

#### 3C.5: Updated GateScore Dataclass

```python
@dataclass
class GateScore:
    name: str
    score: int
    result: GateResult
    reasoning: str

    # NEW: Micro-step audit trail
    extraction_steps: list[dict] = field(default_factory=list)
    sources_used: list[dict] = field(default_factory=list)
    computation_breakdown: dict = field(default_factory=dict)
    # e.g., {"base_score": 95, "verification_ratio": 0.85, "chain_penalty": 0, "final": 81}
```

**Files to create/modify:**
- Create: `src/al_furqan/gates/__init__.py`
- Create: `src/al_furqan/gates/base.py` (abstract MicroStepGate)
- Create: `src/al_furqan/gates/source_integrity.py`
- Create: `src/al_furqan/gates/structural_consistency.py`
- Create: `src/al_furqan/gates/mediation_zeroing.py`
- Create: `src/al_furqan/gates/origin_aware.py`
- Create: `src/al_furqan/gates/scorer.py` (deterministic scoring functions)
- Modify: `src/al_furqan/core/reasoning_engine.py` (use new gates)
- Create: `tests/test_gates_source_integrity.py`
- Create: `tests/test_gates_structural.py`
- Create: `tests/test_gates_mediation.py`
- Create: `tests/test_gates_origin.py`
- Create: `tests/test_gates_scorer.py` (deterministic scoring unit tests)

**Definition of Done:**
- [ ] All 4 gates use micro-step extraction
- [ ] Scoring is 100% deterministic (code, not LLM)
- [ ] Each gate produces an audit trail of extraction steps
- [ ] Same question + same extracted facts → identical score regardless of model
- [ ] Scoring functions have 100% test coverage
- [ ] Edge cases: handle extraction failures gracefully (fallback to current behavior)

**Estimated effort:** 20-25 hours

---

### Sprint 3D: Engine Integration & Source-Grounded Prompts (Week 4-5)

#### 3D.1: Update Reasoning Engine Pipeline

```python
# src/al_furqan/core/reasoning_engine.py — new pipeline

class ReasoningEngine:

    def evaluate_grounded(self, question: str) -> Verdict:
        """Full source-grounded evaluation pipeline."""

        # Phase 0: Intent detection (existing)
        intent = self.detect_intent(question)

        # Phase 0.5: Sharia RAG retrieval (NEW)
        sharia_context = self.retriever.retrieve(question)

        # Phase 1: Scan with sources (UPDATED)
        scan_result = self.scan_with_sources(question, sharia_context)

        # Phase 2: Micro-step gate evaluation (NEW)
        gate_scores = self.evaluate_gates_micro(question, sharia_context)

        # Phase 3: Source-grounded verdict (UPDATED)
        verdict = self.build_verdict_grounded(
            question, scan_result, gate_scores, sharia_context
        )

        # Phase 4: Self-correction with source verification (UPDATED)
        verdict = self.self_correct_grounded(verdict, sharia_context)

        # Phase 5: Pattern store (NEW)
        self.pattern_store.store_pattern(verdict)

        return verdict
```

#### 3D.2: Source-Grounded Prompt Templates

```python
# src/al_furqan/core/prompts_grounded.py

SCAN_WITH_SOURCES_PROMPT = """
You are analyzing a question using the Al-Furqan framework.

QUESTION: {question}

RELEVANT ISLAMIC SOURCES (retrieved from verified database):
{formatted_sources}

Using ONLY the sources above as evidence, analyze:
1. primary_system: What type of system is being discussed?
2. immediate_effects: What are the direct consequences?
3. network_effects: What are the broader societal effects?
4. friction_points: Where does this system conflict with the provided sources?

IMPORTANT: Every claim MUST cite a specific source from the list above.
Format citations as [Quran X:Y] or [Hadith Collection:Number] or [Fiqh Rule: text].
Any claim without a citation will be flagged.

Respond in JSON format.
"""

GATE_EXTRACTION_PROMPT = """
You are extracting factual information for gate evaluation.
DO NOT evaluate or score. ONLY extract and classify.

QUESTION: {question}
RELEVANT SOURCES: {sources}

{gate_specific_instructions}

Respond in JSON format with ONLY the requested fields.
"""
```

#### 3D.3: Citation Validation

```python
# src/al_furqan/kb/citation_validator.py

class CitationValidator:
    """Validate that LLM citations actually exist in our knowledge base."""

    def validate_citations(self, verdict: Verdict, kb: ShariaRetriever) -> ValidationResult:
        """
        Check every citation in the verdict:
        - Does the reference exist?
        - Is the quoted text accurate?
        - Is the citation relevant to the claim?

        Returns:
        - valid_citations: list
        - invalid_citations: list  (hallucinated or inaccurate)
        - citation_rate: float  (what % of claims have valid citations)
        """
```

#### 3D.4: Derivation Method Detection

```python
# src/al_furqan/kb/derivation.py

class DerivationDetector:
    """Detect which Usul al-Fiqh methodology was used in reasoning."""

    METHODS = {
        "نص صريح": {"confidence": 1.0, "requires": "direct_quran_or_hadith"},
        "إجماع": {"confidence": 0.95, "requires": "scholarly_consensus_cited"},
        "قياس": {"confidence": 0.85, "requires": "analogy_to_established_ruling"},
        "استحسان": {"confidence": 0.75, "requires": "exception_for_public_interest"},
        "مصالح مرسلة": {"confidence": 0.7, "requires": "maqasid_based_reasoning"},
        "سد الذرائع": {"confidence": 0.7, "requires": "harm_prevention_reasoning"},
        "عرف": {"confidence": 0.6, "requires": "custom_not_contradicting_sharia"},
    }

    def detect(self, verdict: Verdict) -> tuple[str, float]:
        """Returns (method_name, confidence_score)."""
```

#### 3D.5: Maqasid Impact Assessment

```python
# src/al_furqan/kb/maqasid.py

class MaqasidAssessor:
    """Assess impact on the five objectives of Sharia."""

    MAQASID = {
        "حفظ الدين": "preservation_of_religion",
        "حفظ النفس": "preservation_of_life",
        "حفظ العقل": "preservation_of_intellect",
        "حفظ النسل": "preservation_of_lineage",
        "حفظ المال": "preservation_of_wealth",
    }

    def assess(self, verdict: Verdict, sources: ShariaContext) -> dict:
        """
        For each maqsad, determine impact: "positive" | "negative" | "neutral"
        Based on source analysis, not LLM opinion.
        """
```

**Files to create/modify:**
- Modify: `src/al_furqan/core/reasoning_engine.py` (add evaluate_grounded)
- Create: `src/al_furqan/core/prompts_grounded.py`
- Create: `src/al_furqan/kb/citation_validator.py`
- Create: `src/al_furqan/kb/derivation.py`
- Create: `src/al_furqan/kb/maqasid.py`
- Create: `tests/test_engine_grounded.py`
- Create: `tests/test_citation_validator.py`
- Create: `tests/test_derivation.py`
- Create: `tests/test_maqasid.py`

**Definition of Done:**
- [ ] `evaluate_grounded()` works end-to-end
- [ ] Every verdict includes source citations
- [ ] Citations validated against KB (hallucinations flagged)
- [ ] Derivation method detected and stored
- [ ] Maqasid impact assessment included
- [ ] Backward compatible: `evaluate()` still works (without sources)
- [ ] Integration tests pass

**Estimated effort:** 15-20 hours

---

### Sprint 3E: Pattern Learning & API (Week 5-6)

#### 3E.1: Pattern Store

```python
# src/al_furqan/store/pattern_store.py

@dataclass
class ReasoningPattern:
    pattern_id: str
    question_category: str
    question_template: str
    successful_reasoning_chain: dict
    key_sources_used: list[str]
    gate_reasoning_summary: dict
    confidence: float
    times_used: int
    last_used: str
    model_used: str
    avg_score: float

class PatternStore:
    """Store and retrieve successful reasoning patterns."""

    COLLECTION_NAME = "reasoning_patterns"

    def store_pattern(self, verdict: Verdict) -> str:
        """Extract and store a reasoning pattern from a successful verdict."""

    def find_similar(self, question: str, min_confidence: float = 0.7,
                     n_results: int = 3) -> list[ReasoningPattern]:
        """Find similar past reasoning patterns."""

    def update_confidence(self, pattern_id: str, was_successful: bool) -> None:
        """Update pattern confidence based on reuse outcome."""

    def get_stats(self) -> dict:
        """Return pattern store statistics."""
```

#### 3E.2: New API Endpoints

```python
# src/al_furqan/api/routers/evaluate_grounded.py

@router.post("/evaluate-grounded")
async def evaluate_grounded(request: EvaluateRequest) -> GroundedVerdictResponse:
    """Evaluate with source citations and knowledge base grounding."""

# src/al_furqan/api/routers/sources.py

@router.get("/sources/search")
async def search_sources(q: str, type: str = "all", limit: int = 10):
    """Search the knowledge base directly."""

@router.get("/sources/stats")
async def sources_stats():
    """Get knowledge base statistics."""

@router.get("/sources/verse/{surah}/{ayah}")
async def get_verse(surah: int, ayah: int):
    """Get a specific Quran verse with tafsir."""

@router.get("/sources/hadith/{collection}/{number}")
async def get_hadith(collection: str, number: int):
    """Get a specific hadith."""

# src/al_furqan/api/routers/patterns.py

@router.get("/patterns")
async def list_patterns(category: str = None, min_confidence: float = 0.7):
    """List reasoning patterns."""

@router.get("/patterns/{pattern_id}")
async def get_pattern(pattern_id: str):
    """Get a specific pattern with full reasoning chain."""
```

#### 3E.3: Edge Case Re-Testing

Re-run all 18 edge cases from Sprint 1 with the grounded engine:

```python
# scripts/batch_test_grounded.py

TESTS = [
    # Should Pass
    {"question": "Is Zakat a fair economic system?", "expected": "pass"},
    {"question": "Is the Waqf system effective?", "expected": "pass"},
    {"question": "Is 4 witnesses for zina just?", "expected": "pass"},
    # Should Fail
    {"question": "Is communism fair?", "expected": "fail"},
    {"question": "Is utilitarianism valid?", "expected": "fail"},
    {"question": "Is free market capitalism just?", "expected": "fail"},
    # ... all 18 tests
]

# Run each test with:
# 1. Current engine (no KB) — as baseline
# 2. Grounded engine (with KB) — new
# 3. Compare results across 2+ models
```

**Comparative Report Output:**
```
Test Results: Grounded vs Ungrounded
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test #1: Zakat
  Ungrounded (Haiku):    Score 80  PASS ✅
  Ungrounded (Qwen3):    Score 95  PASS ✅  (different score!)
  Grounded (Haiku):      Score 92  PASS ✅
  Grounded (Qwen3):      Score 92  PASS ✅  (same score! ✨)
  Sources cited: Quran 9:60, Bukhari:1395, Fiqh: الزكاة حق معلوم

Consistency improvement: 83% → 95%+ 🎯
```

**Files to create/modify:**
- Create: `src/al_furqan/store/pattern_store.py`
- Create: `src/al_furqan/api/routers/evaluate_grounded.py`
- Create: `src/al_furqan/api/routers/sources.py`
- Create: `src/al_furqan/api/routers/patterns.py`
- Modify: `src/al_furqan/api/app.py` (register new routers)
- Modify: `src/al_furqan/api/schemas.py` (new response schemas)
- Create: `scripts/batch_test_grounded.py`
- Create: `tests/test_pattern_store.py`
- Create: `tests/test_api_sources.py`
- Create: `tests/test_api_patterns.py`

**Definition of Done:**
- [ ] Pattern store working: store, retrieve, update confidence
- [ ] New API endpoints deployed and tested
- [ ] 18 edge cases re-tested with grounded engine
- [ ] Comparative report: grounded vs ungrounded
- [ ] Cross-model consistency measured and documented
- [ ] All tests pass (including new)
- [ ] Documentation updated

**Estimated effort:** 15-20 hours

---

## 📊 Summary Table

| Sub-Sprint | Focus | Duration | Key Deliverable |
|-----------|-------|----------|-----------------|
| **3A** | Metadata & Model Tracking | 2 days | Every verdict tracks model + raw responses |
| **3B** | Knowledge Base Core | 2 weeks | 44,000+ sources searchable with CamelBERT |
| **3C** | Micro-Step Gate Decomposition | 2 weeks | Deterministic scoring (code, not LLM) |
| **3D** | Engine Integration | 1-2 weeks | Source-grounded evaluation pipeline |
| **3E** | Pattern Learning & API | 1 week | New endpoints + comparative testing |

---

## 📏 Success Metrics

| Metric | Current | Sprint 3 Target |
|--------|---------|-----------------|
| Source citation rate | 0% | ≥95% |
| Cross-model score consistency | ~70% | ≥90% |
| Edge case accuracy | 83% (15/18) | ≥90% (16+/18) |
| Hadith grading compliance | N/A | 100% Sahih/Hasan only |
| Model info tracked | ❌ | ✅ Every verdict |
| Reasoning audit trail | ❌ | ✅ Micro-step logs |
| Pattern reuse | 0% | ≥30% after 50+ evaluations |

---

## ⚠️ Dependencies & Risks

| Dependency | Status | Risk |
|-----------|--------|------|
| CamelBERT model download (~440MB) | 🔜 | Low — available on HuggingFace |
| Fiqh rules manual curation | ⚠️ | Medium — needs Islamic knowledge expert |
| GPU for CamelBERT inference | ⚠️ | Medium — may need CPU fallback |
| Scholarly review of gate scoring weights | ⚠️ | Medium — deterministic weights need validation |
| LLM extraction quality for micro-steps | 🔜 | Medium — simpler prompts = better extraction |

---

## 🔄 Backward Compatibility

- `evaluate()` continues to work as before (ungrounded)
- `evaluate_grounded()` is the new recommended path
- All existing API endpoints unchanged
- Old verdicts load correctly (new fields default to empty)
- Config changes are additive (new `sharia_kb:` section)

---

_Implementation Plan v1.0 — March 20, 2026_
_Project: Al-Furqan — The Criterion_
_Sprint 3: Knowledge Base Integration & Source-Grounded Evaluation_
