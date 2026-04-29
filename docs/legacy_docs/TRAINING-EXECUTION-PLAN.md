# Training Pipeline — Execution Plan
## What to Build, In What Order

---

**Date:** April 5, 2026
**Executor:** Claude Code (implementation) + Muhammad (review/curation)
**Goal:** Build the complete training pipeline from data ingestion to evaluation

---

## Phase 0: Tafsir Data Acquisition (Expand Training Volume)

The existing 9-tafsir consolidated file is a start, but for reasoning-focused
training we need the tafsirs that specifically analyze the Quran's **logical
structure, verse coherence, and argument flow** (ilm al-munasabat).

### 0.1 Ingest Structural Tafsirs from HuggingFace

**Source:** `MohamedRashad/Quran-Tafseer` (84 tafsirs, 219K rows, Apache 2.0)

**Priority tafsirs to extract** (ranked by relevance to reasoning training):

| Priority | Tafsir | Author | Why It Matters |
|----------|--------|--------|---------------|
| **P0** | نظم الدرر في تناسب الآيات والسور | al-Biqa'i | THE book on verse-to-verse logical connections (ilm al-munasabat) |
| **P0** | التحرير والتنوير | Ibn Ashur | Modern, heavy on rhetorical/structural analysis (balagha) |
| **P0** | مفاتيح الغيب (التفسير الكبير) | Fakhr al-Din al-Razi | Rationalist — analyzes arguments structurally, not just traditionally |
| **P1** | الكشاف | al-Zamakhshari | Premier linguistic/rhetorical tafsir — how Quran constructs arguments via language |
| **P1** | البحر المحيط | Abu Hayyan | Deep grammatical commentary — syntactic relationships and rhetorical structure |
| **P1** | في ظلال القرآن | Sayyid Qutb | Holistic — each surah as unified theme with internal coherence |
| **P2** | الميزان في تفسير القرآن | al-Tabatabai | Tafsir al-Quran bi'l-Quran — cross-referencing to build coherent arguments |
| **P2** | جامع البيان | al-Tabari | Foundational — all later tafsirs reference it |
| **P2** | الجامع لأحكام القرآن | al-Qurtubi | Legal reasoning — how scholars extract logical arguments |

**Script:** `scripts/ingestion/ingest_shamela_tafsirs.py`

**Process:**
1. Load HuggingFace dataset (`datasets` library, already in deps)
2. Filter for priority tafsirs by `tafsir_book` name
3. For each verse entry: extract surah, ayah, tafsir_book, tafsir_content
4. Index into new ES index: `furqan_tafsir_structural`
5. Mapping: verse_key (keyword), tafsir_book (keyword), content (text with arabic_furqan analyzer)
6. Generate per-verse reasoning annotations from structural tafsirs

**Volume:** ~219K rows total, ~50K for priority tafsirs alone. Massive increase over current 9 books.

### 0.2 Shamela Direct Access (For Books Missing from HuggingFace)

If Nazm al-Durar (al-Biqa'i) or Al-Tahrir wa'l-Tanwir (Ibn Ashur) are not
in the HuggingFace dataset, use Shamela as backup:

**Option A:** Shamela v4 API (requires API key from shamela.ws)
- Register at dev.shamela.ws
- Download book SQLite databases (IDs: 9098, 9776, 23635, 23627, 23591)
- Parse HTML content → clean Arabic text

**Option B:** Shamela web scraper
- Use `shamela2epub` or custom BeautifulSoup scraper
- Target: shamela.ws/book/{id}/page/{n}

**Option C:** Tarteel QUL (qul.tarteel.ai/resources)
- 114 tafsirs in SQLite/JSON format
- Download and filter for structural tafsirs

---

## Phase 1: Training Infrastructure (Code)

### 1.1 Create `training/` Directory Structure

```
training/
├── __init__.py
├── configs/
│   ├── sft_stage1_qwen35_27b.yaml
│   ├── sft_stage2_qwen35_27b.yaml
│   ├── sft_qwen35_9b.yaml
│   ├── dpo_qwen35_27b.yaml
│   └── eval.yaml
├── data/
│   ├── __init__.py
│   ├── convert_criterion_to_chat.py    # Criterion JSONL → Unsloth chat
│   ├── generate_transition_examples.py # Tokenized Quran → reasoning tasks
│   ├── generate_real_world_scenarios.py # Domain scenarios → chat format
│   ├── generate_tafsir_reasoning.py    # Structural tafsirs → reasoning examples
│   ├── build_dpo_pairs.py              # Feedback → preference pairs
│   └── validate_dataset.py            # Format validation + stats
├── train_sft.py                        # Unsloth SFT (both stages)
├── train_dpo.py                        # TRL DPO
├── eval/
│   ├── __init__.py
│   ├── tafsir_benchmark.py
│   ├── real_world_benchmark.py
│   ├── transition_scorer.py
│   └── questions/
│       ├── tafsir_core.jsonl
│       ├── tafsir_extended.jsonl
│       └── real_world.jsonl
├── export/
│   ├── merge_lora.py
│   └── deploy_ollama.sh
└── requirements.txt
```

### 1.2 Tafsir Ingestion Script

**Script:** `scripts/ingestion/ingest_shamela_tafsirs.py`

**Inputs:**
- HuggingFace `MohamedRashad/Quran-Tafseer` dataset
- (Optional) Shamela SQLite databases for missing books

**Outputs:**
- ES index `furqan_tafsir_structural` with per-verse structural tafsir
- Stats: book count, verse coverage, avg content length

**Dependencies:** `datasets` (already in optional deps)

### 1.3 Convert Criterion Pairs to Chat Format

**Script:** `training/pipeline/converters/criterion_to_chat.py`

**Inputs:**
- `data/lessons/training_pairs/criterion_training_all.jsonl` (2,487 pairs)
- System prompt from `The-Criterion-Prompt.md` + axioms from `engine/axioms.py`
- Tool definitions from `kb/tafsir/kb_tools.py`

**Outputs:**
- `data/training/sft_stage1_train.jsonl`
- `data/training/sft_stage1_val.jsonl`
- `data/training/sft_stage1_test.jsonl`

**Conversion:**
- Each Criterion pair → multi-turn conversation (system/user/tool_call/tool_response/assistant)
- Synthesize tool calls from scan data
- Build tool responses from tafsir_context + verse text
- Final assistant turn = mirror reasoning + verdict

### 1.4 Generate Transition-Aware Examples

**Script:** `training/pipeline/generators/transition_examples.py`

**Inputs:**
- `furqan_quran_tokens` ES index (tokenized verses)
- Structural tafsir data from `furqan_tafsir_structural`

**Outputs:** Appended to `data/training/sft_stage1_train.jsonl`

**Process:**
1. Query ES for verses with interesting transitions:
   - `transition_type != "continuation"` (shifts)
   - `returns_to != -1` (callbacks)
   - `discourse_depth > 0` (nesting)
   - semantic field changes between adjacent words
2. For each verse, pull structural tafsir (al-Biqa'i, Ibn Ashur)
3. Build question: "How does the Quran transition from X to Y in verse Z?"
4. Build answer: identify transition type, logical chain, discourse depth,
   citing the structural tafsir for WHY the transition works

**Target:** 500-1,000 examples.

### 1.5 Generate Tafsir Reasoning Examples

**Script:** `training/pipeline/generators/tafsir_reasoning.py`

**Inputs:**
- Priority structural tafsirs from ES
- Tokenized verse data

**Outputs:** Appended to `data/training/sft_stage1_train.jsonl`

**Process:**
This is the key script that bridges tafsir → reasoning patterns:

1. For each surah/passage, load al-Biqa'i's munasabat analysis
2. Extract the LOGICAL CONNECTIONS he identifies between verses
3. Map each connection to our transition/logic token types
4. Build training examples that teach the model:
   - "In verses X-Y, al-Biqa'i identifies a [transition_type] pattern"
   - "The logical chain is: premise (v.X) → evidence (v.X+1) → conclusion (v.X+2)"
   - "This maps to operators: [condition] → [evidence_shift] → [consequence]"

**Target:** 1,000+ examples from al-Biqa'i + Ibn Ashur + al-Razi.

### 1.6 Real-World Scenario Generator

**Script:** `training/pipeline/generators/real_world.py`

**Inputs:**
- Human-curated scenario templates (written manually or with LLM assistance)
- Quranic reasoning pattern catalog (from tokenizer)

**Outputs:**
- `data/training/sft_stage2_train.jsonl`
- `data/training/sft_stage2_val.jsonl`

**7 domains, 70+ scenarios each:**

| Domain | Patterns Most Applicable |
|--------|------------------------|
| Economics | restriction (ما...إلا), consequence (ف), reductio |
| Governance | condition→response (إذا...ف), accountability chains |
| Ethics | escalation (تصعيد), contrast (مقابلة), gradual corruption |
| Social systems | universal (كل), exception (إلا), evidence_shift |
| Philosophy | reductio, hypothetical (لو), rhetorical_denial (أفلا) |
| Justice | adversative (بل/لكن), restriction, emphasis stacking |
| Science claims | evidence_first, oath→assertion, deductive |

### 1.7 DPO Pair Builder

**Script:** `training/pipeline/generators/dpo_pairs.py`

**Inputs:** Human feedback from pipeline usage

**Outputs:**
- `data/training/dpo_train.jsonl`
- `data/training/dpo_val.jsonl`

### 1.8 Dataset Validator

**Script:** `training/pipeline/validation/validate_dataset.py`

Validates all training data files:
- Correct JSON structure
- All required fields present
- Chat format compatible with Unsloth/Qwen3 template
- No empty conversations
- Arabic text not corrupted
- Token counts within max_seq_length
- Domain balance statistics

---

## Phase 2: Training Scripts

### 2.1 SFT Training Script

**Script:** `training/train_sft.py`

**Usage:**
```bash
# Stage 1: Tafsir baseline
python training/train_sft.py --config training/configs/sft_stage1_qwen35_27b.yaml

# Stage 2: Real-world transfer (starts from Stage 1 checkpoint)
python training/train_sft.py --config training/configs/sft_stage2_qwen35_27b.yaml

# Prototype (local GPU)
python training/train_sft.py --config training/configs/sft_qwen35_9b.yaml
```

**Implementation:** Unsloth FastLanguageModel + TRL SFTTrainer

### 2.2 DPO Training Script

**Script:** `training/train_dpo.py`

**Usage:**
```bash
python training/train_dpo.py --config training/configs/dpo_qwen35_27b.yaml
```

**Implementation:** TRL DPOTrainer on Stage 2 SFT checkpoint

---

## Phase 3: Evaluation Harness

### 3.1 Tafsir Benchmark

**Script:** `training/eval/tafsir_benchmark.py`

87 questions testing tafsir reasoning accuracy, KB tool usage, source attribution.

### 3.2 Real-World Benchmark

**Script:** `training/eval/real_world_benchmark.py`

50+ unseen scenarios testing pattern transfer across domains.

### 3.3 Transition Quality Scorer

**Script:** `training/eval/transition_scorer.py`

Scores model output against tokenized ground truth (transition types,
logical operators, discourse depth).

---

## Execution Order

| Step | What | Depends On | Effort |
|------|------|-----------|--------|
| **0.1** | Ingest structural tafsirs from HuggingFace | ES running | Medium |
| **1.1** | Create training/ directory structure | — | Small |
| **1.3** | Convert Criterion pairs to chat format | 1.1 | Medium |
| **1.4** | Generate transition examples from tokenized Quran | 1.1, ES | Medium |
| **1.5** | Generate tafsir reasoning examples | 0.1, 1.1 | Large |
| **1.8** | Dataset validator | 1.3, 1.4 | Small |
| **2.1** | SFT training script + configs | 1.1 | Medium |
| **1.6** | Real-world scenario generator | 1.1 | Large (human curation needed) |
| **2.2** | DPO training script | 2.1 | Small |
| **3.x** | Evaluation harness | 2.1 | Medium |
| **1.7** | DPO pair builder | Pipeline usage | Medium |

**Critical path:** 0.1 → 1.3/1.4/1.5 → 1.8 → 2.1 (Stage 1 SFT runnable)

---

## Tafsir Data Volume Estimate

| Source | Entries | Unique Verses Covered |
|--------|---------|----------------------|
| Current 9 tafsirs (consolidated) | ~56K | 6,236 (full Quran) |
| HuggingFace 84 tafsirs (all) | ~219K | 6,236 (full Quran) |
| **Priority structural tafsirs (9 books)** | **~50K** | **6,236** |
| Existing Criterion pairs | 2,487 | ~200 unique verses |
| Lesson transcripts (24 episodes) | 2,487 pairs | Surat Al-An'am |

**After ingestion:** ~50K structural tafsir entries + 2,487 Criterion pairs
= massive improvement in reasoning pattern coverage across the full Quran,
not just Surat Al-An'am.

---

_Plan generated: April 5, 2026_
