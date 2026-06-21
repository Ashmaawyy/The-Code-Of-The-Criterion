# Al-Furqan Documentation

This directory is the documentation map for the current Al-Furqan architecture.
Use it together with the root [README](../README.md): the root README is the
quick operational overview; this file tells you where deeper architecture,
storage, security, tokenizer, RAG, and MCP documents live.

---

## Documentation Layers

| Location | Role |
| --- | --- |
| `docs/active_docs/` | Current architecture, implemented subsystem docs, and still-relevant plans |
| `docs/legacy_docs/` | Superseded architecture, sprint reports, session logs, historical training plans |
| `docs/architecture/` | Focused architecture notes, including layer boundaries |
| `docs/proposals/` | Business/proposal artifacts |
| `src/al_furqan/documentation/` | Older module-level internal documentation kept with source |
| `plan/` | PRDs, sprint plans, implementation plans, and roadmap material |

The active architecture baseline is v3.0, with important post-v3 deltas in the
live code and status docs:

- Core runtime storage is Elasticsearch, not ChromaDB/JSON.
- The Quran tokenizer uses Word, Root, Semantic, Logic, and Transition tokens.
- Training/staging data now includes verse graph and human-history JSONL flows.
- `furqan-memory/` intentionally remains local SQLite + ChromaDB.

---

## Active Architecture and Status

| Document | Use for |
| --- | --- |
| [AL-FURQAN-ARCHITECTURE-v3.0](active_docs/AL-FURQAN-ARCHITECTURE-v3.0.md) | Baseline system architecture: layers, gates, chains, Z3, security, MCP skills |
| [PROJECT-STATUS](active_docs/PROJECT-STATUS.md) | Current implementation status and decision log |
| [AL-FURQAN-IMPLEMENTATION-PLAN-v1.0](active_docs/AL-FURQAN-IMPLEMENTATION-PLAN-v1.0.md) | Completed task-level implementation breakdown |
| [the-criterion-formal-axioms.tex](active_docs/the-criterion-formal-axioms.tex) | Formal axiom definitions in LaTeX |
| [README-AL-FURQAN.pdf](active_docs/README-AL-FURQAN.pdf) | Generated/static PDF overview artifact |

---

## Storage, Knowledge, and Retrieval

| Document | Use for |
| --- | --- |
| [ELASTICSEARCH-MIGRATION](active_docs/ELASTICSEARCH-MIGRATION.md) | ES migration rationale, runtime index schemas, analyzer design |
| [AL-FURQAN-KNOWLEDGE-GRAPH-DOCS](active_docs/AL-FURQAN-KNOWLEDGE-GRAPH-DOCS.md) | Knowledge graph schema, edge types, loaders, and visualization notes |
| [KNOWLEDGE-GRAPH-LEARNING-PLAN-v1.0](active_docs/KNOWLEDGE-GRAPH-LEARNING-PLAN-v1.0.md) | LLM-assisted KB graph building for Surat Al-An'am |
| [RAG-IMPLEMENTATION-PLAN-v1.0](active_docs/RAG-IMPLEMENTATION-PLAN-v1.0.md) | Engine-guided RAG design: query analysis, plan building, KB tools, feedback |

Runtime ES schemas are defined in code at
`src/al_furqan/kb/es/indices.py`. Treat that module as authoritative when docs
and code disagree.

---

## Engine, Security, and Tokenizer

| Document | Use for |
| --- | --- |
| [FURQAN-AXIOM-SECURITY-POLICY-v1.0](active_docs/FURQAN-AXIOM-SECURITY-POLICY-v1.0.md) | Prompt guard, axiom integrity, output validation, adapter sandbox, audit logging |
| [QURAN-TOKENIZER-v1.0](active_docs/QURAN-TOKENIZER-v1.0.md) | Multi-level Quran tokenizer and reward-signal design |

Current engine implementation lives under `src/al_furqan/engine/`:

- `axioms.py` anchors axioms and gate definitions.
- `pipeline.py` runs intent detection, Scan, Mirror, Verdict, and self-correction.
- `gates/`, `chains/`, and `symbolic/` hold gate logic, guided questions, scoring,
  predicate extraction, and Z3 verification.
- `security/` holds the five-layer security components.
- `tafsir/` holds guided Tafsir/RAG planning and feedback logic.

---

## MCP Skills

| Document | Use for |
| --- | --- |
| [FURQAN-RAAS-DOCS](active_docs/FURQAN-RAAS-DOCS.md) | Implemented reasoning MCP server details |
| [FURQAN-REASONING-AS-A-SKILL-v1.0](active_docs/FURQAN-REASONING-AS-A-SKILL-v1.0.md) | RaaS architecture specification |
| [FURQAN-MEMORY-DOCS](active_docs/FURQAN-MEMORY-DOCS.md) | Implemented local memory MCP server details |
| [FURQAN-MEMORY-SKILL-v1.0](active_docs/FURQAN-MEMORY-SKILL-v1.0.md) | Memory skill architecture specification |
| [FURQAN-SKILLS-IMPLEMENTATION-PLAN-v1.0](active_docs/FURQAN-SKILLS-IMPLEMENTATION-PLAN-v1.0.md) | Historical implementation roadmap for both MCP packages |

The package-level READMEs are the quickest current references:

- [furqan-raas README](../furqan-raas/README.md)
- [furqan-memory README](../furqan-memory/README.md)

---

## Training and Fine-Tuning

Active training references are split between the current code and older plans:

| Artifact | Status |
| --- | --- |
| `training/pipeline/` | Current graph/history extraction and ES staging pipeline |
| [FINE-TUNING-IMPLEMENTATION-PLAN-v1.0.pdf](active_docs/FINE-TUNING-IMPLEMENTATION-PLAN-v1.0.pdf) | Active PDF-only fine-tuning artifact |
| [FURQAN-TRAINING-PRD-v1.0](legacy_docs/FURQAN-TRAINING-PRD-v1.0.md) | Historical PRD, superseded by later implementation choices |
| [FURQAN-TRAINING-IMPLEMENTATION-PLAN-v1.0](legacy_docs/FURQAN-TRAINING-IMPLEMENTATION-PLAN-v1.0.md) | Historical technical plan |
| [FINE-TUNING-IMPLEMENTATION-PLAN-v1.0](legacy_docs/FINE-TUNING-IMPLEMENTATION-PLAN-v1.0.md) | Historical Markdown version |

The generated training data layout is documented in
[data_archive/README.md](../data_archive/README.md).

---

## Legacy Documentation

Legacy documents are preserved for audit trail and project memory. Do not treat
them as current architecture unless a current document points back to them.

| Document | Date / role |
| --- | --- |
| [AL-FURQAN-ARCHITECTURE-v2.0](legacy_docs/AL-FURQAN-ARCHITECTURE-v2.0.md) | Superseded architecture |
| [SPRINT-2-DOCUMENTATION](legacy_docs/SPRINT-2-DOCUMENTATION.md) | Sprint 2 history |
| [SPRINT-3-5-ENGINE-DOCS](legacy_docs/SPRINT-3-5-ENGINE-DOCS.md) | Engine refactor history |
| [SPRINT-6-SECURITY-DOCS](legacy_docs/SPRINT-6-SECURITY-DOCS.md) | Security sprint history |
| [SPRINT-REPORT-2026-03-22](legacy_docs/SPRINT-REPORT-2026-03-22.md) | RAG sprint history |
| [DAILY-REPORT-2026-03-21](legacy_docs/DAILY-REPORT-2026-03-21.md) | Sprints 3-6 execution report |
| [SESSION-REPORT-2026-03-19](legacy_docs/SESSION-REPORT-2026-03-19.md) | First session record |
| [SESSION-REPORT-2026-03-29-30](legacy_docs/SESSION-REPORT-2026-03-29-30.md) | ES migration/tokenizer session record |
| [LESSON-PIPELINE-REPORT-2026-03-29](legacy_docs/LESSON-PIPELINE-REPORT-2026-03-29.md) | Lesson pipeline report |
| [LINTING-CHANGELOG](legacy_docs/LINTING-CHANGELOG.md) | Linting audit trail |
| [TRAINING-EXECUTION-PLAN](legacy_docs/TRAINING-EXECUTION-PLAN.md) | Historical training execution notes |

---

## Maintenance Rules

- When changing architecture, update the root README, this docs index, and the
  affected package README in the same patch.
- When changing ES schemas, update `src/al_furqan/kb/es/indices.py` first, then
  refresh docs that describe indices.
- When changing archive or training paths, update `src/al_furqan/paths.py`,
  `data_archive/README.md`, and any pipeline command examples.
- Keep legacy docs immutable except for broken-link repair or explicit archival
  notes.
