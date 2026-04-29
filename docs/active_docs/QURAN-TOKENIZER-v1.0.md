# Al-Furqan Multi-Level Quran Tokenizer — v1.0

## Purpose

The tokenizer produces a **certainty=1.0 reference encoding** of the entire
Quran at 5 linguistic levels.  This encoding serves as the ground-truth
anchor for training reward signals — teaching an LLM what perfect text
generation looks like in terms of meaning consistency, logical structure,
and idea-transition quality.

The Quran is the only Arabic text corpus that satisfies all three properties
simultaneously:
1. **Zero ambiguity** — every word and diacritical mark is fixed by ijma
2. **Perfect preservation** — mutawatir transmission across 1400+ years
3. **Multi-level annotation** — centuries of scholarly morphological,
   syntactic, and semantic analysis

---

## Architecture

```
furqan_quran (ES)                  furqan_qac_morphology (ES)
   │ verse text                        │ expert annotations
   ▼                                   ▼
┌──────────────────────────────────────────────────┐
│                    encoder.py                     │
│                                                   │
│  Level 1: WordToken        ← word splitting       │
│  Level 2A: RootToken       ← morphology.py (QAC)  │
│  Level 2B: SemanticToken   ← semantics.py         │
│  Level 2C: LogicToken      ← semantics.py         │
│  Level 3: TransitionToken  ← semantics.py         │
│                                                   │
│  Output: VerseTokens (certainty=1.0)              │
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
              furqan_quran_tokens (ES)
```

> **Phonetic layer removed:** The tokenizer deliberately does not encode
> tajweed, phonemes, or pronunciation.  The training signal teaches the LLM
> how the Quran transitions between ideas — not how it sounds.

---

## The 5 Tokenization Levels (Word → Root → Semantic → Logic → Transition)

### Level 1 — Word (`WordToken`)

Raw surface form in mushaf order.

| Field | Type | Example (بِسْمِ) |
|-------|------|-----------------|
| `position` | int | 0 |
| `surface` | str | `بِسْمِ` (with diacritics) |
| `surface_clean` | str | `بسم` (stripped) |
| `is_stop_word` | bool | false |

**Training signal:** Sequence prediction — given this word, what comes next
in the mushaf?  Teaches the model coherent text flow.

### Level 2A — Root (`RootToken`)

Morphological decomposition into trilateral root, pattern, and affixes.

| Field | Type | Example (ٱلرَّحِيمِ) |
|-------|------|---------------------|
| `root` | str | `ر-ح-م` |
| `root_letters` | list | `["ر", "ح", "م"]` |
| `pattern` | str | `فَعِيل` |
| `pos` | str | `ADJ` |
| `prefixes` | list | `["ال"]` |
| `suffixes` | list | `[]` |
| `lemma` | str | `رحيم` |

**Training signal:** Semantic grounding — the model learns that `كِتَاب`,
`مَكْتُوب`, `كَاتِب` share root `ك-ت-ب` and thus share meaning.  Current
BPE tokenizers miss this entirely.

**Data source:** Primary lookup from QAC corpus (expert-annotated, 100%
accurate for Quranic text).  Rule-based fallback for non-Quranic text.

### Level 2B — Semantic (`SemanticToken`)

What the word *means* in context — not just what it's made of.

| Field | Type | Example (ٱلرَّحِيمِ) |
|-------|------|---------------------|
| `semantic_field` | str | `mercy` |
| `pattern_meaning` | str | `permanent_quality` |
| `syntactic_role` | str | `attribute` |
| `referent` | str | (what a pronoun points to) |
| `scope` | str | `word` / `clause` / `verse` |

**Semantic fields (13):**
divinity, mercy, worship, belief, guidance, knowledge, justice, creation,
legislation, social, eschatology, morality, narrative

**Pattern meanings (18):**
base_action, intensive, mutual, causative, reflexive, cooperative,
passive_become, seeking, quality, request, agent, patient, instrument,
place, permanent_quality, excessive, comparative, abstract_noun

**Training signal:** Conceptual consistency — rewards the model for choosing
words from the correct semantic domain.  Penalizes drift into unrelated
vocabulary mid-argument.

### Level 2C — Logic (`LogicToken`)

How the word functions in the reasoning structure.

| Field | Type | Example (لَوْ) |
|-------|------|---------------|
| `operator` | str | `hypothetical` |
| `role_in_argument` | str | `condition` |
| `connects_to` | list[int] | `[6]` (links to response) |
| `negation_scope` | list[int] | (positions negated) |
| `emphasis_level` | float | 0.0 – 1.0 |

**Logical operators (25):**
conjunction, sequence, consequence, disjunction, adversative, condition,
condition_response, hypothetical, universal, restriction, exception,
negation, emphasis, oath, result, question, rhetorical_denial, command,
prohibition, exhortation, anaphora, cataphora, demonstrative

**Multi-word pattern detection:**
- `مَا...إِلَّا` → restriction (حصر)
- `إِنَّ...لَ` → emphasis stacking (0.5 + 0.3 = 0.8)
- `إِذَا/إِنْ...فَ` → condition → response (شرط وجواب)

**Training signal:** Reasoning structure — the model learns *how* arguments
are built (premise → evidence → conclusion), not just *what* to say.

### Level 3 — Transition (`TransitionToken`)

How the discourse moves from one idea to the next.

| Field | Type | Example |
|-------|------|---------|
| `transition_type` | str | `pivot` / `contrast` / `escalation` / ... |
| `source_idea` | str | semantic field *before* this point |
| `target_idea` | str | semantic field *after* this point |
| `smoothness` | float | 1.0 (Quran ground truth = perfectly smooth) |
| `discourse_depth` | int | nesting level of the current argument |
| `returns_to` | int | position of an earlier idea being echoed (-1 = none) |

**Transition types (10):**
continuation, pivot, contrast, escalation, conclusion, evidence_shift,
parenthetical, callback, new_scene, question_answer

**Training signal:** Idea-transition quality — the model learns *how* to
move between concepts smoothly while maintaining logical robustness.
This is the core learning objective: the Quran's ability to shift topics,
introduce evidence, contrast ideas, and return to earlier themes with
perfect coherence.

> **Design note:** The phonetic/tajweed layer has been deliberately removed.
> Mimicking the Quran's sound is forbidden; learning its reasoning
> architecture is the goal.

---

## QAC Corpus Integration

The Quranic Arabic Corpus provides expert-annotated morphological data for
every word in the Quran.  It is extracted from the project's PostgreSQL dump
(`mini_quran_dev.sql`) and indexed into Elasticsearch.

### Extraction Pipeline

```bash
# Parse SQL dump → index into furqan_qac_morphology
python -m al_furqan.tokenizer.qac_extractor
```

### Tables Extracted

| Table | Records | Data |
|-------|---------|------|
| `quran.roots` | ~1,800 | Root letters, trilateral form, frequency |
| `quran.lemmas` | ~5,000 | Dictionary forms, translations |
| `quran.words` | ~78,000 | Surface form, verse_key, position, root_id, lemma_id |
| `quran.morphology_word_segments` | ~200,000 | POS tags, grammar descriptions, verb forms |

### Two-Tier Lookup

```
analyze_word("ٱللَّهِ", verse_key="1:1", position=2)
    │
    ├─ Tier 1: QAC lookup (ES: furqan_qac_morphology)
    │          → exact root, POS, lemma, verb form
    │          → 100% accurate for Quranic text
    │
    └─ Tier 2: Rule-based fallback
               → prefix/suffix stripping + consonantal skeleton
               → ~80% accuracy (for non-Quranic text)
```

---

## Usage

### Encode the entire Quran

```bash
# Prerequisites: ES running, furqan_quran index populated

# Encode all 6,236 verses
python -m al_furqan.tokenizer.encoder

# Encode one surah
python -m al_furqan.tokenizer.encoder --surah 1

# Inspect a single verse (detailed output)
python -m al_furqan.tokenizer.encoder --verse 2:255
```

### Output Format (per verse)

```json
{
  "verse_key": "1:1",
  "text_ar": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
  "certainty": 1.0,
  "word_tokens": [
    {"position": 0, "surface": "بِسْمِ", "surface_clean": "بسم", "is_stop_word": false}
  ],
  "root_tokens": [
    {"position": 0, "root": "س-م-و", "pattern": "فِعْل", "pos": "N", "prefixes": [], "suffixes": []}
  ],
  "semantic_tokens": [
    {"position": 0, "semantic_field": "none", "pattern_meaning": "abstract_noun", "syntactic_role": "topic"}
  ],
  "logic_tokens": [
    {"position": 0, "operator": "none", "role_in_argument": "", "emphasis_level": 0.0}
  ],
  "transition_tokens": [
    {"position": 0, "transition_type": "none", "source_idea": "", "target_idea": "creation", "smoothness": 1.0, "discourse_depth": 0, "returns_to": -1}
  ],
  "word_count": 4,
  "unique_roots": 4,
  "reasoning_pattern": "none",
  "position_in_mushaf": 0
}
```

### ES Index

All tokenized data is stored in `furqan_quran_tokens` with nested mappings
for each level, queryable by root, POS, semantic field, transition type, etc.

---

## Reward Signal Formula

For training, the model's output is scored against the Quran's 5-level
tokenization.  The phonetic component has been removed and its weight
redistributed to logic and transition — the two layers that capture
the Quran's reasoning architecture.

```
Score = α·S_word + β·S_root + γ·S_semantic + δ·S_logic + τ·S_transition

where:
  S_word       = sequence match against mushaf word order
  S_root       = root+pattern match (concept consistency)
  S_semantic   = semantic field coherence (staying on domain)
  S_logic      = logical structure match (argument quality)
  S_transition = idea-transition quality (smooth flow between concepts)

Suggested weights:
  α = 0.10  (surface form)
  β = 0.20  (root/meaning)
  γ = 0.20  (semantic field coherence)
  δ = 0.25  (logical reasoning structure)
  τ = 0.25  (idea transition smoothness & robustness)
```

The Quran reference always scores 1.0 on all components.  The model's
output is scored relative to this anchor — closer to the reference patterns
means higher reward.

**Note:** δ + τ = 0.50 — half the total reward comes from logical structure
and idea transitions.  This is by design: the LLM should learn the Quran's
reasoning architecture, not its surface form.

---

## Future Work

1. **Full QAC integration** — run `qac_extractor.py` to populate
   `furqan_qac_morphology` from the SQL dump for 100% root accuracy
2. **Syntactic parsing** — full i'rab roles (beyond POS-based heuristics)
3. **Cross-verse transitions** — detect idea transitions that span multiple
   verses (e.g., a parenthetical that opens in one ayah and closes in another)
4. **Passage-level reasoning classification** — assign `ReasoningPattern`
   at the ruku/passage level
5. **Training pipeline** — DPO pair generation using the 5-level scores,
   with heavy weighting on logic + transition quality
6. **Transition pattern library** — catalog recurring transition patterns
   across the entire Quran (e.g., oath → evidence → conclusion)
