# PRD Addendum: Islamic Sharia Knowledge Base Integration
## Al-Furqan — The Criterion
### Version 1.0 | Sprint 3

---

## 1. Executive Summary

This addendum extends the Al-Furqan reasoning engine with a **Sharia Knowledge Base (SKB)** — a vectorized corpus of Islamic primary sources (Quran, Hadith, Tafsir, Fiqh rules) that transforms the engine from an LLM-dependent reasoner into a **source-grounded Islamic reasoning system**.

**The core shift:** From "AI opinion based on training data" → "AI judgment grounded in verified Islamic sources with citations."

### Key Metrics
| Metric | Current | Target |
|--------|---------|--------|
| Source citation rate | 0% | 95%+ |
| Accuracy on Islamic questions | ~70% | ~95% |
| Verifiability | None (black box) | Every verdict traceable to source |
| Response consistency | Varies by LLM | Stable (anchored to sources) |

---

## 2. Problem Statement

### 2.1 Current Limitations
1. **No source grounding**: The engine says "Islam prohibits X" without citing Quran/Hadith
2. **LLM bias dependency**: Results vary based on which LLM is used and its training data
3. **No verification path**: Users cannot verify the engine's Islamic reasoning
4. **Shallow understanding**: LLMs know *what* Islam says but not *how* scholars derive rulings
5. **Pattern amnesia**: Each evaluation starts fresh — no learning from prior verdicts

### 2.2 What This Solves
- Every verdict backed by specific Quranic verses and authentic hadith
- Consistent results regardless of LLM provider
- Transparent reasoning chain: Question → Source → Derivation → Verdict
- Accumulating intelligence through pattern learning

---

## 3. Proposed Architecture

### 3.1 System Overview

```
┌──────────────────────────────────────────────────────┐
│                    User Question                      │
└───────────────────────┬──────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────┐
│              Phase 0: Intent Detection                │
│         (informational / system_eval / claim)         │
└───────────────────────┬──────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────┐
│          Phase 0.5: Sharia RAG Retrieval       [NEW]  │
│                                                       │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌────────┐ │
│  │ Quran   │  │ Hadith  │  │ Tafsir   │  │ Fiqh   │ │
│  │ Vector  │  │ Vector  │  │ Vector   │  │ Rules  │ │
│  │ Store   │  │ Store   │  │ Store    │  │ Store  │ │
│  └────┬────┘  └────┬────┘  └────┬─────┘  └───┬────┘ │
│       └────────────┼───────────┘              │      │
│                    ▼                          │      │
│           Semantic Search                     │      │
│           + Cross-Reference                   │      │
│           + Relevance Scoring ◄───────────────┘      │
└───────────────────────┬──────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────┐
│      Phase 1-4: Scan → Mirror → Verdict → Correct    │
│                                                       │
│  Now with:                                            │
│  • Source citations in gate reasoning                 │
│  • Fiqh rules mapped to gates                         │
│  • Derivation methodology (Usul al-Fiqh)             │
└───────────────────────┬──────────────────────────────┘
                        ▼
┌──────────────────────────────────────────────────────┐
│           Phase 5: Pattern Store              [NEW]   │
│                                                       │
│  • Store successful reasoning chains                  │
│  • Index by topic, gates, sources used                │
│  • Build precedent library (case law)                 │
│  • Feed back into future evaluations                  │
└──────────────────────────────────────────────────────┘
```

### 3.2 Knowledge Base Schema

#### 3.2.1 Quran Collection
```json
{
    "surah_number": 5,
    "surah_name_ar": "المائدة",
    "surah_name_en": "Al-Ma'idah",
    "ayah_number": 90,
    "text_ar": "يَا أَيُّهَا الَّذِينَ آمَنُوا إِنَّمَا الْخَمْرُ وَالْمَيْسِرُ...",
    "text_en": "O you who have believed, indeed, intoxicants...",
    "tafsir_ibn_kathir": "...",
    "tafsir_al_jalalain": "...",
    "tafsir_al_saadi": "...",
    "asbab_al_nuzul": "...",
    "topics": ["alcohol", "gambling", "prohibition", "social"],
    "rulings_derived": ["prohibition of intoxicants"],
    "gate_relevance": {
        "source_integrity": 0.9,
        "structural_consistency": 0.7,
        "mediation_zeroing": 0.8,
        "origin_aware": 1.0
    }
}
```

#### 3.2.2 Hadith Collection
```json
{
    "collection": "sahih_bukhari",
    "book": "Book of Faith",
    "hadith_number": 1,
    "narrator_chain": "عن عمر بن الخطاب رضي الله عنه",
    "text_ar": "إنما الأعمال بالنيات...",
    "text_en": "Actions are but by intentions...",
    "grading": "sahih",
    "grading_scholar": "Al-Bukhari",
    "topics": ["intention", "sincerity", "actions"],
    "fiqh_implications": ["niyyah required for worship"],
    "cross_references": {
        "quran": ["2:225", "3:145"],
        "other_hadith": ["muslim:1907"]
    }
}
```

#### 3.2.3 Fiqh Rules Collection
```json
{
    "rule_ar": "الأمور بمقاصدها",
    "rule_en": "Matters are judged by their intentions",
    "category": "القواعد الخمس الكبرى",
    "evidence_quran": ["2:225"],
    "evidence_hadith": ["bukhari:1", "muslim:1907"],
    "sub_rules": [
        "لا ثواب إلا بنية",
        "العبرة في العقود بالمقاصد والمعاني"
    ],
    "applications": [
        "Contracts judged by intent, not just wording",
        "Worship requires sincere intention"
    ],
    "gate_mapping": {
        "primary_gate": "mediation_zeroing",
        "reasoning": "Strips human surface behavior, evaluates against intended purpose"
    }
}
```

#### 3.2.4 Reasoning Pattern Collection
```json
{
    "pattern_id": "pat_001",
    "question_category": "economic_system",
    "question_template": "Is {system} a fair economic system?",
    "successful_reasoning_chain": {
        "scan_approach": "Identify economic principles and compare to Zakat/Sadaqah model",
        "key_sources_used": ["quran:2:275", "bukhari:1395", "rule:la_darar"],
        "gate_reasoning": {
            "source_integrity": "Compare claimed benefits against empirical evidence + Quranic economic principles",
            "structural_consistency": "Map to Islamic economic structure (Zakat cycle, prohibition of riba)",
            "mediation_zeroing": "Check if system relies on human preference or divine guidance"
        },
        "verdict_approach": "Evaluate against maqasid al-shariah (preservation of wealth)"
    },
    "confidence": 0.92,
    "times_used": 5,
    "last_used": "2026-03-19"
}
```

---

## 4. Feature Specifications

### 4.1 Sharia RAG Retrieval Engine

**Purpose:** Given a question, retrieve the most relevant Quran verses, hadith, tafsir passages, and fiqh rules.

**Retrieval Strategy:**
1. **Semantic search**: Embed question → find nearest sources in vector space
2. **Topic-based retrieval**: Extract topics from question → match tagged sources
3. **Cross-reference expansion**: If a verse is found, pull related hadith and fiqh rules
4. **Relevance scoring**: Score each result by gate relevance

**Configuration:**
```yaml
sharia_kb:
  quran:
    collection: "quran_verses"
    tafsir_sources: ["ibn_kathir", "al_jalalain", "al_saadi"]
    retrieval_count: 10
  hadith:
    collection: "hadith_corpus"
    min_grading: "hasan"  # Only hasan and sahih
    retrieval_count: 15
  fiqh:
    collection: "fiqh_rules"
    retrieval_count: 5
  patterns:
    collection: "reasoning_patterns"
    retrieval_count: 3
    min_confidence: 0.7
  embedding:
    model: "CAMeL-Lab/bert-base-arabic-camelbert-ca"
    fallback: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    chunk_size: 512
    overlap: 50
```

### 4.2 Source-Grounded Gate Evaluation

**Current prompt (Scan):**
```
Analyze the following question...
```

**New prompt (Scan with sources):**
```
Analyze the following question using ONLY the provided Islamic sources as evidence.

RELEVANT SOURCES:
[Quran] Al-Ma'idah 5:90 — "O you who have believed, indeed intoxicants..."
[Hadith] Sahih Muslim 2003 — "Every intoxicant is wine, and every wine is forbidden"
[Fiqh Rule] "الضرر يزال" — Harm must be eliminated
[Pattern] Similar question "alcohol prohibition" scored 100, Origin: Survive

You MUST cite specific sources in your reasoning. Any claim without a source citation 
is treated as ungrounded speculation.
```

### 4.3 Derivation Methodology (Usul al-Fiqh Integration)

The engine will learn **how scholars derive rulings**, not just what rulings exist:

**Derivation Methods (prioritized):**
1. **نص صريح (Explicit Text)** — Direct Quran/Hadith statement → Highest confidence
2. **إجماع (Consensus)** — Scholarly agreement → Very high confidence
3. **قياس (Analogical Reasoning)** — Derive from similar case → High confidence
4. **استحسان (Juristic Preference)** — Exception to analogy for public interest → Medium confidence
5. **مصالح مرسلة (Public Interest)** — No explicit text, but serves Maqasid → Medium confidence
6. **سد الذرائع (Blocking Means)** — Preventing harm before it occurs → Medium confidence
7. **عرف (Custom)** — Local practice if not contradicting Sharia → Lower confidence

**Integration with Gates:**
| Derivation Method | Gate Relevance |
|-------------------|----------------|
| نص صريح | Source-Integrity (max score) |
| إجماع | Structural-Consistency (high score) |
| قياس | All gates (demonstrated reasoning) |
| استحسان | Mediation-Zeroing (human noise audit) |
| مصالح مرسلة | Origin-Aware (tests transcendent grounding) |

### 4.4 Pattern Learning & Accumulation

**How it works:**
1. After each successful evaluation, extract the reasoning chain
2. Identify which sources were most relevant
3. Store as a searchable pattern with confidence score
4. Future similar questions retrieve and build on prior patterns

**Pattern Lifecycle:**
```
New Question → Search Patterns → Found Similar?
    │                                    │
    │ No                                 │ Yes
    ▼                                    ▼
Full Evaluation                    Pre-loaded Context
    │                              (prior reasoning + sources)
    ▼                                    │
Store New Pattern ◄──────────────────────┘
    │
    ▼
Update Confidence (if reused successfully)
```

### 4.5 Maqasid al-Shariah Mapping

Map every evaluation to the **five objectives of Sharia**:

| Maqsad | Arabic | Gate Mapping |
|--------|--------|-------------|
| Preservation of Religion | حفظ الدين | Origin-Aware |
| Preservation of Life | حفظ النفس | Structural-Consistency |
| Preservation of Intellect | حفظ العقل | Source-Integrity |
| Preservation of Lineage | حفظ النسل | Mediation-Zeroing |
| Preservation of Wealth | حفظ المال | Structural-Consistency |

Every verdict will include a **Maqasid Impact Assessment**.

---

## 5. Data Pipeline

### 5.1 Ingestion Pipeline

```
Raw Sources (JSON/CSV/API)
    ↓
Data Validation & Cleaning
    ↓
Arabic Text Normalization (tashkeel, hamza)
    ↓
Chunking (ayah-level, hadith-level, rule-level)
    ↓
Embedding Generation (CamelBERT)
    ↓
ChromaDB / Qdrant Insertion
    ↓
Cross-Reference Indexing
    ↓
Topic Tagging (auto + manual review)
    ↓
Gate Relevance Scoring
```

### 5.2 Quality Assurance

1. **Hadith Grading Filter**: Only Sahih and Hasan hadith used as evidence
2. **Tafsir Source Ranking**: Ibn Kathir > Al-Jalalain > Al-Saadi (configurable)
3. **Cross-Validation**: Claims must be supported by 2+ sources minimum
4. **Human Review Queue**: Edge cases flagged for scholarly review
5. **Version Control**: All source data versioned (git-lfs or DVC)

---

## 6. API Changes

### 6.1 New Endpoints

```
POST /api/v1/evaluate-grounded
    Body: { "question": "...", "require_sources": true }
    Response: { verdict + source_citations[] }

GET /api/v1/sources/search
    Query: ?q=alcohol+prohibition&type=quran,hadith
    Response: { sources[] with relevance scores }

GET /api/v1/sources/stats
    Response: { total_quran, total_hadith, total_fiqh, total_patterns }

GET /api/v1/patterns
    Query: ?category=economic_system&min_confidence=0.8
    Response: { patterns[] }
```

### 6.2 Enhanced Verdict Response

```json
{
    "verdict_id": "verdict_xxx",
    "dual_perspective": true,
    "system_verdict": {
        "score": 100,
        "gate_scores": [...],
        "source_citations": [
            {
                "type": "quran",
                "reference": "Al-Ma'idah 5:90",
                "text_ar": "...",
                "relevance": 0.95,
                "used_in_gate": "source_integrity"
            },
            {
                "type": "hadith",
                "reference": "Sahih Muslim 2003",
                "grading": "sahih",
                "relevance": 0.91,
                "used_in_gate": "structural_consistency"
            }
        ],
        "derivation_method": "نص صريح",
        "derivation_confidence": 0.98,
        "maqasid_impact": {
            "preservation_of_intellect": "positive",
            "preservation_of_life": "positive",
            "preservation_of_wealth": "neutral"
        },
        "similar_patterns_used": ["pat_001"]
    }
}
```

---

## 7. Implementation Plan

### Sprint 3A: Core Knowledge Base (2 weeks)
- [ ] Download and validate Quran + Tafsir datasets
- [ ] Download and validate Hadith datasets (filter Sahih/Hasan)
- [ ] Set up CamelBERT embedding pipeline
- [ ] Build ChromaDB collections (quran, hadith, tafsir)
- [ ] Implement `ShariaKnowledgeBase` class with retrieval methods
- [ ] Write ingestion scripts with validation
- [ ] Unit tests for retrieval accuracy

### Sprint 3B: Integration with Engine (2 weeks)
- [ ] Update Scan prompt to include retrieved sources
- [ ] Update Mirror prompt to require source citations
- [ ] Update Verdict prompt to include derivation methodology
- [ ] Add `source_citations` field to Verdict dataclass
- [ ] Implement cross-reference expansion
- [ ] Add Maqasid impact assessment
- [ ] Integration tests

### Sprint 3C: Pattern Learning (1 week)
- [ ] Implement `PatternStore` class
- [ ] Extract reasoning chains from successful verdicts
- [ ] Build pattern matching and retrieval
- [ ] Add confidence scoring and update logic
- [ ] Pattern-based context injection in evaluations

### Sprint 3D: Fiqh Rules & Methodology (1 week)
- [ ] Manually curate 50 core fiqh rules (القواعد الفقهية)
- [ ] Map derivation methods to gate scoring
- [ ] Implement Usul al-Fiqh methodology layer
- [ ] Add derivation confidence scoring

### Sprint 3E: API & Testing (1 week)
- [ ] New API endpoints (evaluate-grounded, sources/search, patterns)
- [ ] Enhanced verdict response with citations
- [ ] Re-run 18 edge cases with grounded evaluation
- [ ] Comparative report: before/after knowledge base
- [ ] Documentation update

---

## 8. Success Criteria

| Criteria | Target |
|----------|--------|
| Source citation in verdicts | ≥95% of verdicts include ≥1 Quran/Hadith citation |
| Citation accuracy | ≥98% of citations are relevant to the question |
| Hadith grading compliance | 100% — only Sahih/Hasan used as evidence |
| Edge case accuracy improvement | ≥90% correct (up from 83%) |
| Pattern reuse rate | ≥30% of evaluations leverage prior patterns |
| Response time | <60s for grounded evaluation (vs ~30s current) |
| Maqasid coverage | 100% of verdicts include Maqasid impact assessment |

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Incorrect hadith grading in dataset | Critical | Use only verified datasets (LK Corpus, Sahih collections) |
| Tafsir disagreements between scholars | High | Present multiple tafsir, let engine weigh them |
| Embedding model poor at Classical Arabic | High | Use CamelBERT (trained on Classical Arabic) |
| Over-reliance on RAG (ignoring engine logic) | Medium | Sources inform but don't override gate logic |
| Dataset bias (e.g., only one madhab) | Medium | Include cross-madhab sources |
| Storage requirements | Low | Start with MVP (~650MB), scale as needed |

---

## 10. Future Extensions (Post-Sprint 3)

1. **Fatwa Database**: Integration with IslamQA.info and major fatwa institutions
2. **Scholarly Video Annotations**: Timestamped annotations of lecture content
3. **Multi-Madhab Support**: Present different scholarly opinions with reasoning
4. **Arabic Query Understanding**: Native Arabic question processing (not just English)
5. **Isnad Analysis**: Automated hadith narrator chain verification
6. **Fine-tuning**: Use curated data to fine-tune domain-specific embedding model
7. **Real-time Scholar Feedback**: Loop for scholars to correct and improve verdicts

---

## 11. Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| ChromaDB | ✅ Already integrated | Extend with new collections |
| CamelBERT model | 🔜 Need to download | ~440MB model |
| Quran datasets | 🔜 Available on HuggingFace | See sources catalog |
| Hadith datasets | 🔜 Available on HuggingFace | 300k+ records |
| Fiqh rules | ⚠️ Manual curation needed | 50 rules for MVP |
| Scholarly review | ⚠️ Need domain expert | For annotation quality |

---

_PRD Addendum v1.0 — Proposed by Muhammad Al-Ashmawy (@ashmaaawy)_
_Architecture: Mahmoud Al-Samman (@MahmoudSamman)_
_Date: 2026-03-19_
