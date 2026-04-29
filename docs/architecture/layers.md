# Al-Furqan: Project Layers

One page that tells any new contributor — or future-you — where code belongs
and why. If you're adding a new script, fetcher, generator, or library
module, this document decides the directory.

---

## Principle: one layer per concern

The project is split into four concentric layers. A dependency arrow points
**inward**: outer layers may import from inner layers, never the reverse.

```
┌──────────────────────────────────────────────────────────────┐
│  scripts/         one-off + entrypoint CLIs                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  training/pipeline/   pipeline stages (batch jobs)     │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  src/al_furqan/   runtime library + engine       │  │  │
│  │  │  ┌────────────────────────────────────────────┐  │  │  │
│  │  │  │  data_archive/   static reference data    │  │  │  │
│  │  │  └────────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

- **`data_archive/`** — static, mostly-read data. Quran, hadith, graph
  snapshots, training JSONL outputs, archived source material. Primary
  source of truth at seed time; ES is the runtime source of truth.
- **`src/al_furqan/`** — the runtime library and reasoning engine. Imported
  by every other layer. Must not depend on anything above it.
- **`training/pipeline/`** — batch pipeline stages. Imports from the
  library; never imported by it.
- **`scripts/`** — entrypoint CLIs. One-shot fetchers, loaders, and
  administrative tools. Runnable directly with `python scripts/.../foo.py`.

---

## Where does my new file go?

### `scripts/` — one-off CLIs and entrypoints

Runnable entrypoint scripts, each with its own `__main__` block. Not imported
by other code. Each subdirectory is grouped by *what the script does*, not
by what domain it touches.

| Directory | Purpose | Example |
|---|---|---|
| `scripts/fetch/` | External data retrieval — Wikipedia, Gutenberg, YouTube transcripts, RAND/CFR/CRS reports, etc. Writes to `data_archive/`. | `scripts/fetch/fetch_data.py` |
| `scripts/neo4j/` | Load JSONL into Neo4j. Each loader is a one-shot; shared driver boilerplate lives in `_neo4j.py`. | `scripts/neo4j/load_neo4j.py` |
| `scripts/rendering/` | Render visual artifacts (architecture diagrams, graph images). Non-DB rendering only — the neo4j loaders moved out. | `scripts/rendering/render_architecture_diagrams.py` |
| `scripts/kb_extraction/` | LLM-driven extraction jobs (relationship extraction, edge proposals). Writes to the proposed-edges review DB. | `scripts/kb_extraction/lesson_edges_llm_processor.py` |
| `scripts/eval/` | Evaluation and benchmark runners. Reads verdict store, writes reports. | `scripts/eval/run_full_evaluation.py` |
| `scripts/benchmarks/` | Performance benchmarks. | `scripts/benchmarks/run_kb_benchmark.py` |

**Rule:** if the file is invoked with `python ...` as a top-level command and
its output is a side effect on disk or a service, it belongs in `scripts/`.

### `training/pipeline/` — batch pipeline stages

Code that runs as part of the training data build pipeline. Organized by
*stage* (what it produces), not by domain.

| Directory | Stage | Produces |
|---|---|---|
| `training/pipeline/extractors/` | Edge extraction from static sources — one file per edge type (tafsir, hadith, sira, lesson, crossref, transition). Shared `types.py` + `loaders.py`. | Per-verse edge lists in memory |
| `training/pipeline/generators/` | Assemble training/testing JSONL files from extractor output or raw text. One generator = one output JSONL. | `data_archive/training/*.jsonl` |
| `training/pipeline/staging/` | ES bulk load. Reads JSONL, writes to ES indices. Imports its plan from `src/al_furqan/kb/es/indices.py`. | ES indices populated |
| `training/pipeline/sira_db/` | Static reference data for Sira events, stored as Python constants. Treated as data even though it's `.py`. | Constants imported by `sira_edges.py` |
| `training/pipeline/graph_builder.py` | Top-level orchestrator that runs all extractors and writes the quran graph JSONL. | `data_archive/training/quran_graph.jsonl` |

**Rule:** pipeline code reads raw data and writes intermediate artifacts.
It never talks to the runtime engine. Invoked with `python -m
training.pipeline.<something>`.

### `src/al_furqan/` — runtime library and engine

Core library. This is what gets imported by everything else. Subpackages are
split by architectural role.

| Subpackage | Role |
|---|---|
| `al_furqan.paths` | **Central filesystem constants.** Every module that needs a path imports from here. One rename = one file change. |
| `al_furqan.config` | User-level configuration (`USER_DATA_ROOT`, `AppConfig`). *Not* the repo root — see `paths.PROJECT_ROOT` for that. |
| `al_furqan.engine/` | The Criterion reasoning engine: gates, scoring, correction passes, audit logging. |
| `al_furqan.kb/` | Knowledge-base layer — everything the engine reads from at runtime. |
| `al_furqan.kb.es/` | Elasticsearch client, analyzers, index definitions (`indices.py` — the single registry), migrators (`migrate_data.py`, `migrate_verdicts.py`, `migrate_embeddings.py`), offline cache (`cache.py`), snapshot tool (`snapshot.py`), retrievers. |
| `al_furqan.kb.ingestion/` | Library code for turning raw sources into domain models (NOT executable fetchers — those are in `scripts/fetch/`). |
| `al_furqan.kb.graph/` | Graph schema definitions. |
| `al_furqan.kb.tafsir/` | Tafsir query tools. |
| `al_furqan.providers/` | LLM provider abstractions (Ollama, OpenAI-compatible, etc). |
| `al_furqan.store/` | Verdict and feedback stores (ES-backed). |
| `al_furqan.tokenizer/` | Arabic tokenization utilities. |
| `al_furqan.api/` | FastAPI layer. |
| `al_furqan.lessons/` | Lesson processing pipeline config. |
| `al_furqan.documentation/` | Docstring-style docs for the library. |

**Rule:** if it's imported by the engine at runtime, or by a script or
pipeline stage, it belongs here. Must not import from `scripts/` or
`training/pipeline/`.

### `data_archive/` — static reference data

Not code. Static files committed to git:

- `quran/`, `hadith/`, `graph/`, `lessons/` — canonical reference data
- `human_history/` — raw source material from external fetchers
- `training/` — generated training/testing JSONL outputs
- `external/` — third-party source files (QAC SQL, etc.)
- `review/` — proposed-edge SQLite DB for human review
- `audit/`, `feedback/`, `tafsir_feedback/` — runtime logs that accumulate
- `.es_cache/` — gitignored ES snapshot cache (rebuildable from `snapshot.py`)

This directory used to be called `data/`. It was renamed to signal that ES
is the **runtime** source of truth and these files are the **archive** —
loaded into ES at seed time, fallback-able via `kb.es.cache`, but never the
live read path for the engine.

---

## Naming collisions to avoid

- **`PROJECT_ROOT`** means the repo root. Import it from `al_furqan.paths`.
  The user-level home directory is `al_furqan.config.USER_DATA_ROOT`. These
  are different things. Do not rename or alias them back to the same name.
- **`ingestion`** — `al_furqan.kb.ingestion/` is *library code* for
  transforming data into domain models. `scripts/fetch/` is *executable
  fetchers* (the word "ingestion" used to cover both, hence the rename).
  Library side is ingestion-as-transformation; script side is
  ingestion-as-retrieval. Keep them separate.
- **`PipelineConfig`** in `al_furqan.lessons.config` is the *lesson*
  pipeline config, not the training pipeline config. The training pipeline
  does not currently have a single config object — each stage imports what
  it needs from `al_furqan.paths` and `al_furqan.kb.es.indices`.

---

## Historical notes (why the layout is what it is)

- Originally `scripts/ingestion/` and `scripts/rendering/` existed with
  overlapping responsibilities. `rendering/` contained both neo4j loaders
  and a diagram renderer; the neo4j loaders moved to `scripts/neo4j/`.
  `scripts/ingestion/` was renamed to `scripts/fetch/` to eliminate the
  collision with `al_furqan.kb.ingestion/`.
- `training/pipeline/es_cache.py` and `es_snapshot.py` originally lived
  with the training pipeline but were infrastructure, not training logic.
  They moved to `src/al_furqan/kb/es/cache.py` and `snapshot.py`.
- `training/pipeline/extractors/base.py` originally mixed path constants,
  domain types, and I/O loaders. It was split into `types.py` (domain
  types) and `loaders.py` (I/O). Path constants moved to
  `al_furqan.paths`.
- `training/pipeline/staging/index_training_data.py` originally duplicated
  ES index mapping definitions that already existed in
  `src/al_furqan/kb/es/indices.py`. The mappings were unified there and
  the staging script is now a thin runner that imports
  `TRAINING_INDEX_PLAN` from the registry.
