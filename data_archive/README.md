# Al-Furqan Data Archive

This directory holds archived source material and generated training exports.
It is not the runtime database. Elasticsearch is the runtime query and storage
layer for the core system; this directory is the filesystem side of the data
pipeline.

---

## Current Role in the Architecture

```text
Archived/static source material
  -> ingestion and extraction code
  -> generated JSONL under data_archive/training/
  -> Elasticsearch runtime and training/staging indices
  -> engine, RAG, review, and evaluation flows
```

Do not hand-edit generated JSONL. Change the source corpus, extractor, or
generator and rebuild the output.

---

## Current Top-Level Layout

| Path | Role |
| --- | --- |
| `backup_for_stored_data/` | Static corpus snapshot: Quran, Hadith, Tafsir, lessons |
| `human_history/` | Raw human-history source material from books, reports, articles, and transcripts |
| `training/` | Generated JSONL used by learning/testing and ES staging |
| `README.md` | This file |

Important path note: code-level constants in `src/al_furqan/paths.py` define
normalized archive anchors such as `data_archive/quran`,
`data_archive/hadith`, `data_archive/lessons`, and `data_archive/training`.
This checkout currently keeps the static corpus snapshot under
`backup_for_stored_data/`. When running static-data migration, either normalize
the archive layout or pass `--data-dir data_archive/backup_for_stored_data`.

---

## Static Corpus Snapshot

`backup_for_stored_data/` currently contains:

| Path | Purpose |
| --- | --- |
| `quran/` | Quran source files, including `quran_complete.json` and QAC-related data |
| `hadith/` | Hadith source snapshot |
| `tafsir/` | Tafsir source snapshot |
| `lessons/` | Enriched lesson material used by KB/RAG pipelines |

These files are source snapshots for ingestion and should be treated as
canonical inputs unless a newer normalized archive path is created.

---

## Generated Training Data

`data_archive/training/` is the project-level generated-data location used by
`src/al_furqan/paths.py`.

Current visible outputs:

| Path | Purpose |
| --- | --- |
| `training/learning/model_learning_how_people_learn_from_history.jsonl` | Learning examples about historical reasoning |
| `training/learning/model_learning_quran_graph.jsonl` | Learning examples derived from Quran graph structure |
| `training/testing/model_testing_how_people_talk_about_history.jsonl` | Testing/evaluation examples for historical discourse |
| `training/testing/model_testing_how_people_write_about_history.jsonl` | Testing/evaluation examples for written historical discourse |

The staging code also expects these well-known JSONL outputs when generated:

| Path | Producer |
| --- | --- |
| `training/quran_graph.jsonl` | `python -m training.pipeline.graph_builder` |
| `training/human_history.jsonl` | Human-history generator pipeline |
| `training/testing/model_testing_how_people_talk_about_history.jsonl` | Testing generator pipeline |

---

## Elasticsearch Indices

Runtime index definitions live in `src/al_furqan/kb/es/indices.py`.

| Logical name | Default ES index | Purpose |
| --- | --- | --- |
| `quran` | `furqan_quran` | Quran verses and metadata |
| `hadith` | `furqan_hadith` | Hadith records and grading metadata |
| `graph` | `furqan_graph` | Knowledge graph edges and provenance |
| `lessons` | `furqan_lessons` | Enriched lesson chapters and linked evidence |
| `verdicts` | `furqan_verdicts` | Evaluation verdicts and precedent retrieval |
| `feedback` | `furqan_feedback` | Human feedback and corrections |

Training/staging index plan:

| Key | ES index | Source JSONL |
| --- | --- | --- |
| `graph` | `furqan_graph_edges` | `training/quran_graph.jsonl` |
| `history` | `furqan_history_events` | `training/human_history.jsonl` |
| `testing_talk_about_history` | `furqan_testing_talk_about_history` | `training/testing/model_testing_how_people_talk_about_history.jsonl` |

---

## Common Commands

Create runtime indices:

```bash
python -m al_furqan.kb.es.setup_indices --test
```

Migrate static corpus snapshot into ES:

```bash
python -m al_furqan.kb.es.migrate_data --data-dir data_archive/backup_for_stored_data --verify
```

Build the verse-centric graph JSONL:

```bash
python -m training.pipeline.graph_builder
python -m training.pipeline.graph_builder --extractors tafsir,sira
```

Index generated training JSONL:

```bash
python -m training.pipeline.staging.index_training_data --dry-run
python -m training.pipeline.staging.index_training_data --only graph
python -m training.pipeline.staging.index_training_data --force
```

---

## Data Handling Rules

- Avoid broad recursive globbing; this archive can contain large source files.
- Keep raw source snapshots immutable unless a data-cleaning task explicitly
  says otherwise.
- Regenerate derived JSONL from pipeline code instead of patching records by
  hand.
- Keep Arabic text exact. Do not strip diacritics, transliterate, stem, or
  normalize outside the tokenizer/analyzer code paths.
- Use Elasticsearch status and count commands to verify ingestion rather than
  assuming files are indexed.
