# Al-Furqan - The Criterion

> Axiom-anchored neuro-symbolic reasoning engine for evaluating claims,
> systems, and frameworks against immutable logical axioms grounded in verified
> Islamic scholarship.

Al-Furqan is not a general chatbot. It is a reasoning system whose job is to
separate judgment from generation:

```text
The code routes and scores.
The LLM extracts, reasons, and explains.
Z3 checks formal consistency.
Elasticsearch retrieves verified knowledge and stores verdicts.
Humans review and correct.
```

The canonical Criterion flow remains four sequential gates:

1. Source-Integrity
2. Structural-Consistency
3. Mediation-Zeroing
4. Origin-Aware

The current implementation also carries an `Origin-Preservation` verdict field
as a preservation extension in the engine, API schemas, and ES verdict store.

---

## Current Architecture

```text
Client surfaces
  CLI: al-furqan
  REST: FastAPI under /api/v1
  MCP: furqan-raas reasoning server
  MCP: furqan-memory local memory server

Security envelope
  API keys, role-aware auth, rate limiting, request limits, security headers
  PromptGuard, IntegrityVerifier, OutputValidator, AdapterSandbox, AuditLogger

Orchestration
  FastAPI routers and Orchestrator connect engine, KB, stores, Z3, and LLMs.
  Cross-layer access should happen here, not inside the engine or KB.

Reasoning engine
  Immutable axioms and SHA-256 integrity checks
  Intent detection, Scan -> Mirror -> Verdict -> Self-Correction
  Dual-perspective evaluation for embedded assumptions
  Independent gate modules, guided chains, deterministic scoring
  Symbolic verifier and predicate extraction over Z3
  Tafsir RAG planner, templates, feedback loop, and tool execution

Knowledge and retrieval
  ES-backed Quran, Hadith, graph, lessons, verdicts, and feedback indices
  Arabic analyzer defined in al_furqan.kb.es.analyzers
  Tafsir KB tools exposed to the guided RAG pipeline
  Multi-level Quran tokenizer: Word, Root, Semantic, Logic, Transition
  Ingestion and review path for proposed graph edges

Data and learning
  data_archive/ stores archived/static source material and generated JSONL
  training/pipeline builds verse-centric graph and history training exports
  Runtime verdict/feedback persistence lives in Elasticsearch
  furqan-memory remains local-only SQLite + ChromaDB by design
```

Only orchestration should know about every layer. The engine receives context
as text and returns verdict objects; the KB returns retrieval context; stores
persist and retrieve verdict/feedback documents.

---

## Runtime Surfaces

| Surface | Entry point | Responsibility |
| --- | --- | --- |
| CLI | `al-furqan` | Local command-line access to the core package |
| REST API | `uvicorn al_furqan.api.app:app` | Evaluation, grounded evaluation, Criterion tests, verdict review, stats, health |
| RaaS MCP | `python -m furqan_raas.mcp_server` | JSON-RPC/MCP wrapper for reasoning tools |
| Memory MCP | `python -m furqan_memory.mcp_server` | Local agent memory, recall, pattern recognition, feedback |

Main REST endpoints are mounted under `/api/v1`:

| Endpoint | Purpose |
| --- | --- |
| `POST /evaluate` | Run the standard evaluation pipeline |
| `POST /evaluate/grounded` | Evaluate with retrieved precedent/context |
| `GET /evaluate/{verdict_id}` | Read evaluation result/status |
| `POST /criterion-test` | Evaluate a named framework |
| `GET /verdicts` | List verdicts |
| `GET /verdicts/search` | Search verdicts |
| `GET /verdicts/{verdict_id}` | Read one verdict |
| `DELETE /verdicts/{verdict_id}` | Invalidate a verdict and cascade flags |
| `POST /verdicts/{verdict_id}/review` | Approve, reject, or correct a verdict |
| `GET /stats` | Store statistics |
| `GET /health` | API, store, and LLM health |

---

## Storage and Search

Elasticsearch is the runtime storage and retrieval backend for the core system.
The registry in `src/al_furqan/kb/es/indices.py` defines these runtime indices:

| Logical name | Default ES index | Purpose |
| --- | --- | --- |
| `quran` | `furqan_quran` | Quran verses, Arabic/English text, metadata, embeddings |
| `hadith` | `furqan_hadith` | Hadith records, grading, narration metadata, embeddings |
| `graph` | `furqan_graph` | Knowledge graph edges and provenance |
| `lessons` | `furqan_lessons` | Enriched lesson chapters and linked evidence |
| `verdicts` | `furqan_verdicts` | Evaluation results and precedent retrieval |
| `feedback` | `furqan_feedback` | Human feedback and corrections |

Training/staging indices are also defined in code:

| Plan key | ES index | Source JSONL |
| --- | --- | --- |
| `graph` | `furqan_graph_edges` | `data_archive/training/quran_graph.jsonl` |
| `history` | `furqan_history_events` | `data_archive/training/human_history.jsonl` |
| `testing_talk_about_history` | `furqan_testing_talk_about_history` | `data_archive/training/testing/model_testing_how_people_talk_about_history.jsonl` |

The current checkout has archived raw corpora under
`data_archive/backup_for_stored_data/`. Code-level path constants in
`src/al_furqan/paths.py` define normalized anchors such as
`data_archive/quran`, `data_archive/hadith`, and `data_archive/lessons`; pass
`--data-dir` to migration commands when working from the backup snapshot.

---

## Project Layout

```text
al-furqan/
  src/al_furqan/
    api/                 FastAPI app, routers, schemas, orchestrator
    auth/                API key auth, roles, rate limiting, security middleware
    core/                Backward-compatible re-exports for the engine package
    engine/              Axioms, gates, chains, symbolic verifier, security, Tafsir RAG
    kb/                  ES collections, graph schema, ingestion, Tafsir KB tools
    lessons/             Transcription, cleaning, enrichment helpers
    providers/           LLM provider abstraction
    review/              Human review helpers
    store/               ES verdict and feedback stores
    tokenizer/           Quran tokenizer and QAC-aware morphology
  tests/                 Core package tests
  furqan-raas/           MCP reasoning server wrapper
  furqan-memory/         Local MCP memory server
  data_archive/          Archived corpora and generated training JSONL
  training/              Graph/history extraction and staging pipelines
  scripts/               Benchmarks, evals, fetchers, KB extraction, Neo4j, rendering
  docs/                  Active and legacy documentation
  plan/                  PRDs, sprint plans, and roadmap documents
```

Current tree snapshot from this checkout:

| Area | Count |
| --- | ---: |
| Core Python modules under `src/al_furqan` | 110 |
| Core test modules under `tests` | 42 |
| RaaS test modules | 1 |
| Memory test modules | 4 |
| Test functions across core/RaaS/Memory | 684 |

---

## Quick Start

```bash
pip install -e ".[dev]"
pytest -m "not slow"
ruff check src/ tests/
al-furqan
```

### Conda package

Create the development environment with:

```bash
conda env update --file environment.yml --name al-furqan
conda activate al-furqan
```

Build the local Conda package with `conda-build`:

```bash
conda install -c conda-forge conda-build
conda build conda.recipe
```

The GitHub Actions workflow builds the package on pushes and pull requests
and stores the resulting artifact. Publishing to Anaconda should be added as a
separate release job using an `ANACONDA_API_TOKEN` repository secret.

Run the API:

```bash
uvicorn al_furqan.api.app:app --reload
```

Run Elasticsearch and supporting services:

```bash
docker compose up elasticsearch redis
```

Create and inspect runtime ES indices:

```bash
python -m al_furqan.kb.es.setup_indices --test
python -m al_furqan.kb.es.setup_indices --status
```

Migrate static data into ES, pointing to the current backup snapshot if needed:

```bash
python -m al_furqan.kb.es.migrate_data --data-dir data_archive/backup_for_stored_data --verify
```

Index training JSONL outputs:

```bash
python -m training.pipeline.staging.index_training_data --dry-run
python -m training.pipeline.staging.index_training_data --only graph
```

Operational note: `docker-compose.yml` includes an `es-seed` service, but the
current `Dockerfile.es-seed` still references a legacy `data/` directory and a
`scripts/seed_es.sh` file that is not present in this checkout. Use the explicit
commands above until that container path is reconciled.

---

## Documentation

Start with [docs/README.md](docs/README.md). The most useful active documents:

| Document | Role |
| --- | --- |
| [AL-FURQAN-ARCHITECTURE-v3.0](docs/active_docs/AL-FURQAN-ARCHITECTURE-v3.0.md) | Baseline architecture plus post-v3 update notes |
| [PROJECT-STATUS](docs/active_docs/PROJECT-STATUS.md) | Latest project status and decisions |
| [ELASTICSEARCH-MIGRATION](docs/active_docs/ELASTICSEARCH-MIGRATION.md) | ES migration rationale and schemas |
| [QURAN-TOKENIZER-v1.0](docs/active_docs/QURAN-TOKENIZER-v1.0.md) | Current tokenizer architecture |
| [RAG-IMPLEMENTATION-PLAN-v1.0](docs/active_docs/RAG-IMPLEMENTATION-PLAN-v1.0.md) | Engine-guided RAG design |
| [FURQAN-AXIOM-SECURITY-POLICY-v1.0](docs/active_docs/FURQAN-AXIOM-SECURITY-POLICY-v1.0.md) | Security model |
| [FURQAN-RAAS-DOCS](docs/active_docs/FURQAN-RAAS-DOCS.md) | Reasoning MCP docs |
| [FURQAN-MEMORY-DOCS](docs/active_docs/FURQAN-MEMORY-DOCS.md) | Local memory MCP docs |

The architecture document is still the baseline source of truth, but the live
code has post-v3 updates: ES is the core backend, the tokenizer uses
`TransitionToken` rather than a phonetic/tajweed layer, and training now includes
graph/history staging outputs.

---

## Architecture Rules

- Do not normalize, strip, transliterate, or stem Arabic text outside the
  tokenizer/analyzer paths that already define this behavior.
- Do not edit axiom definitions without updating the anchored SHA-256 integrity
  expectations.
- Route LLM calls through `providers/`; avoid raw provider HTTP calls in feature
  code.
- Keep layer boundaries: orchestration connects engine, KB, stores, and security.
- Treat `furqan-memory/` as local client memory, not core engine storage.
- Treat generated JSONL as rebuildable pipeline output; edit sources or
  extractors instead.

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3.10+ |
| API | FastAPI, uvicorn |
| Tasks/cache | Celery + Redis in dependencies; Redis in compose |
| LLM providers | Anthropic, DashScope/Qwen, Ollama, OpenAI-compatible |
| Formal verification | Z3 SMT solver |
| Runtime storage/search | Elasticsearch 8.x with custom Arabic analyzer |
| Local memory skill | SQLite + ChromaDB |
| Optional embeddings | sentence-transformers / MiniLM-style 384-dim vectors |
| Optional transcription | faster-whisper |
| Graph tooling | ES graph edges; Neo4j loaders for visualization/exploration |

---

## License / Classification

Apache-2.0
