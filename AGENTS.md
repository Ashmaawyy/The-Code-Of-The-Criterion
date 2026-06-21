# al-furqan

Axiom-anchored neuro-symbolic reasoning engine ("The Criterion"). Evaluates ideas, claims, and frameworks against immutable logical axioms rooted in Islamic scholarship (Quran, Hadith, Fiqh, Tafsir), combining formal verification (Z3 SMT) with LLM reasoning and human-in-the-loop feedback.

## Core concept

Four sequential evaluation gates — **Source-Integrity → Structural-Consistency → Mediation-Zeroing → Origin-Aware**. See `The-Criterion-Prompt.md` for the full engine prompt; the `/the-criterion` slash command runs this flow interactively.

## Stack

- Python ≥3.10 (developed on 3.12)
- FastAPI + uvicorn (API), Celery + Redis (tasks)
- Z3 SMT solver (formal gates)
- Elasticsearch 8.x with Arabic analyzer (6 indices) — see `docker-compose.yml` and `Dockerfile.es-seed`
- sentence-transformers, faster-whisper (optional extras)
- Multi-provider LLM: DashScope/Qwen, Anthropic, Ollama, OpenAI-compatible

## Layout

- `src/al_furqan/` — main package (engine/, kb/, tokenizer/, providers/, store/, api/)
- `tests/` — ~705 tests; `pytest.ini_options` in `pyproject.toml` pins `pythonpath=["src"]`
- `plan/` — PRDs, ARCHITECTURE-v2, IMPLEMENTATION-PLAN, SPRINT-*-PLAN.md (sprints 2, 3, 3-4-5 roadmap)
- `docs/active_docs/` — architecture, RAG pipeline, security, fine-tuning, tokenizer
- `docs/legacy_docs/` — historical, ignore unless explicitly asked
- `furqan-memory/`, `furqan-raas/` — memory store and reasoning-as-a-service sub-modules
- `scripts/` — benchmarks, eval, KB extraction, neo4j loaders, rendering
- `training/`, `data_archive/` — fine-tuning datasets (large; don't glob blindly)
- `config.yaml` — runtime configuration

## Common commands

```bash
pip install -e ".[dev]"              # dev setup (add ,embeddings,transcribe,graph,datasets or use [all])
pytest                                # run all tests
pytest -m "not slow"                 # skip slow tests
pytest --cov=src/al_furqan           # with coverage
ruff check src/ tests/               # lint
al-furqan                            # CLI entry point (src/al_furqan/cli.py)
docker-compose up                    # Elasticsearch + seed
```

## Quirks & gotchas

- **Arabic text handling is first-class.** Don't normalize, strip diacritics, or transliterate without checking `tokenizer/`. The tokenizer has 5 levels: Word → Root → Semantic → Logic → Transition.
- **Axiom integrity is SHA-256 anchored.** Do not edit axiom files without updating their hashes; the prompt-guard / output-validator layers will reject tampered inputs.
- **5-layer security model** (prompt guard → axiom integrity → output validator → adapter sandbox → audit logger). When adding LLM calls, route through the provider abstraction in `providers/`, not raw HTTP clients.
- **Elasticsearch must be running** for most integration tests and the API. Seed container in `Dockerfile.es-seed`.
- **Sprint plans are authoritative for scope** — check `plan/SPRINT-*-PLAN.md` before starting multi-file work; the roadmap overrides ad-hoc issue lists.

## Working notes

- User prefers: root-cause fixes over symptomatic patches; critical review over agreeable RLHF-style responses; Plan mode for multi-hour sprints.
- For evaluation / gate-testing tasks, use the `/the-criterion` skill rather than reconstructing the prompt.
- User signs authored documents bilingually — see user memory.
