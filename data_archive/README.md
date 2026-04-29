# Al-Furqan — Data Directory

This directory holds two kinds of material:

1. **Raw source corpora** (Quran, tafsir, hadith, sira, lessons) — the
   canonical inputs that everything else is derived from.
2. **Generated training data** (`training/*.jsonl`) — materialized SFT,
   LM, DPO, and sira datasets produced by the scripts under
   `training/pipeline/`. These are regenerated from the raw sources on
   demand; they are not hand-edited.

All of this also lives in Elasticsearch after indexing (see
`training/pipeline/staging/index_training_data.py`). The file system is
the source of truth for raw corpora; Elasticsearch is the query layer.

---

## Training dataset

| File | Rows | Format |
|---|---|---|
| `training/tafsir_pairs.jsonl` | ~188,000 | Clean ayah→tafsir pairs |

Each line is a direct mapping from a Quran verse to one tafsir book's
explanation of that verse. No template wrapping, no synthetic Q&A —
just the raw scholarly content paired with the verse it explains.

```json
{
  "verse_key": "2:255",
  "surah": 2, "ayah": 255,
  "verse_text_ar": "ٱللَّهُ لَآ إِلَٰهَ إِلَّا هُوَ ...",
  "tafsir_book": "تفسير القرآن العظيم/ ابن كثير",
  "tafsir_scholar": "ابن كثير",
  "tafsir_era": "774 هـ",
  "tafsir_text": "...",
  "source": "es_structural"
}
```

**Sources** (deduplicated, structural tafsirs take priority):

| Source | Pairs | Description |
|---|---|---|
| `furqan_tafsir_structural` (ES) | ~40,000 | 11 priority structural tafsirs (al-Biqa'i, Ibn Ashur, al-Razi, etc.) |
| `furqan_tafsir` (ES) | ~148,000 | 84 classical tafsirs from HuggingFace dataset |

**Regenerate** via `python -m training.pipeline.generators.tafsir_pairs`
(requires ES to be healthy, or `--offline` for local JSON fallback).

### Removed legacy files

All template-generated Q&A chat training data has been removed. The
synthetic chat wrapping (system/user/assistant templates over tafsir
chunks) added noise rather than signal — it taught the model to
regurgitate tafsir in chat format rather than internalize the reasoning.
Removed files (preserved in git history):

- `tafsir_reasoning.jsonl` — 403K templated Q&A chat pairs
- `real_world_examples.jsonl` — 35K templated modern-scenario chat pairs
- `sira_chronological.jsonl` — 14K templated sira chat pairs
- `lessons_training.jsonl` — 2K templated lesson chat pairs
- `quran_mushaf_sequences.jsonl` — 1K mushaf LM sequences
- `dpo_train.jsonl` / `dpo_val.jsonl` — 100K DPO preference pairs
- `sft_stage1_*.jsonl` / `sft_stage2_*.jsonl` — staged splits of the above

---

## Raw source corpora (not regenerated, never edited)

| Path | Size | Description |
|------|------|-------------|
| `quran/quran_complete.json` | ~4 MB | Full Quran: Arabic + English + Meccan/Medinan tag per verse |
| `tafsir/al_tabari.json` | ~12 MB | al-Tabari's *Jami' al-Bayan* |
| `tafsir/tafsir_ibn_kathir.json` | ~10 MB | Ibn Kathir |
| `tafsir/tafsir_al_qurtubi.json` | ~12 MB | al-Qurtubi's *al-Jami'* |
| `tafsir/tafsir_al_tahrir.json` | ~14 MB | Ibn Ashur's *al-Tahrir wa al-Tanwir* |
| `tafsir/tafsir_al_baghawi.json` | ~6 MB | al-Baghawi |
| `tafsir/tafsir_al_saadi.json` | ~2 MB | al-Saadi |
| `tafsir/al_muyassar.json` | ~1 MB | al-Muyassar (King Fahd Complex) |
| `tafsir/al_waseet.json` | ~5 MB | al-Waseet |
| `tafsir/tafsirs_arabic_consolidated.json` | ~63 MB | All 10+ tafsirs keyed by verse, 1923 verses |
| `external/mini_quran_dev.sql` | ~870 MB | QAC morphological database dump |
| `hadith/hadith_sample.json` | ~1 MB | Hadith sample collection (needs expansion for RAG) |
| `lessons/lessons_enriched_json/` | ~8 MB | Enriched teacher lesson transcripts |

### Sira events DB (Python source, hand-curated)

Lives under `training/pipeline/sira_db/`, not here — because it is
authored source, not raw ingested data. Split into period files for
reviewability:

- `schema.py` — 6-axis controlled vocabulary (pressure_type,
  parties, stakes, response_category, principle_class, polarity)
- `meccan.py` — 150 events, orders 1-150 (early/middle/late Meccan)
- `medinan_early.py` — 150 events, orders 151-300 (years 1-3 AH)
- `medinan_middle.py` — 200 events, orders 301-500 (years 4-6 AH, Khandaq / Qurayza / Hudaybiyyah)
- `medinan_late.py` — 150 events, orders 501-650 (years 7-11 AH, Khaybar / Fath / Tabuk / farewell hajj / death)
- `asbab.py` — 150 events, orders 651-800 (specific asbab al-nuzul by surah order)
- `db.py` — loader that concatenates all above and validates tags

Current total: **800 events** with full 6-axis structural tags, zero validation errors.
Distribution: Meccan 26% / Medinan 74% (matches classical asbab literature).

---

## Elasticsearch indices

### RAG indices (runtime retrieval for inference)

| Index | Docs | Purpose |
|---|---|---|
| `furqan_quran` | 6,236 | Every verse with Arabic + English + revelation type |
| `furqan_quran_tokens` | 418,516 | 5-level tokenized Quran (root / lemma / pos / semantic field / logic operator) |
| `furqan_tafsir` | 165,369 | Classical tafsir chunks (one doc per chunk, keyed by verse) |
| `furqan_tafsir_structural` | 39,802 | Structural tafsir re-organized by `tafsir_book`, `surah`, `ayah`, `content`, `content_length`, `priority` |
| `furqan_hadith` | 55 | Hadith (nearly empty — needs expansion) |
| `furqan_lessons` | 2,434 | Teacher lesson transcripts |
| `furqan_graph` | 95 | Knowledge graph edges |

**Gap:** no `furqan_rag_sira` index yet (sira is only in the training
index). Should be added so the model can retrieve sira events at inference
time as described in `training/pipeline/sira_db/db.py`.

**Gap:** no dense-vector fields on any RAG index — retrieval is BM25 only.

### Training index

| Index | Docs | Source |
|---|---|---|
| `furqan_train_tafsir_pairs` | ~188,000 | `tafsir_pairs.jsonl` |

Rebuild via `python -m training.pipeline.staging.index_training_data`.
By default the indexer **upserts** into existing indices; pass `--force`
to drop and recreate from scratch.

---

## Generation pipeline

| Output | Generated by | ES dependency |
|---|---|---|
| `tafsir_pairs.jsonl` | `training/pipeline/generators/tafsir_pairs.py` | ES (or `--offline` for local JSON fallback) |

The generator reads ayah→tafsir pairs directly from ES indices
(`furqan_tafsir_structural` and `furqan_tafsir`), cross-references
verse text from `quran_complete.json`, deduplicates by (verse, book),
and writes clean JSONL. No templates, no chat wrapping.

### Full rebuild

```bash
# 1. Generate ayah→tafsir training pairs (requires ES)
python -m training.pipeline.generators.tafsir_pairs

# 2. Push training data to ES (requires ES)
python -m training.pipeline.staging.index_training_data
```

---

## Initial ES setup (first-time only)

```bash
# 1. Start Elasticsearch (4GB heap minimum)
docker compose up -d elasticsearch

# 2. Create RAG indices with Arabic analyzer
python -m al_furqan.kb.es.setup_indices --test

# 3. Migrate static data (Quran, Hadith, Graph, Lessons)
python -m al_furqan.kb.es.migrate_data --verify

# 4. Ingest tafsir from HuggingFace + structural tafsirs
python -m al_furqan.kb.es.ingest_tafsir_hf
python scripts/ingestion/fetch_data.py tafsirs

# 5. Encode tokenized Quran (5-level tokenization)
python -m al_furqan.tokenizer.encoder

# 6. Generate ayah→tafsir training pairs
python -m training.pipeline.generators.tafsir_pairs

# 7. Index training pairs into ES
python -m training.pipeline.staging.index_training_data

# 8. Verify
python -m al_furqan.kb.es.setup_indices --status
```

### Docker Compose auto-seeding

When running via `docker compose up`, the `es-seed` service
automatically seeds ES after the container is healthy. It runs all
phases above (setup → static data → tafsir → tokenizer → training
pairs) and exits. The seed is idempotent — existing data is upserted,
not dropped. See `Dockerfile.es-seed` and `scripts/seed_es.sh`.
