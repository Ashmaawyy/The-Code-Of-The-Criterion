# Al-Furqan Documentation Index

Documentation is split into two directories:

- **`active_docs/`** — Current architecture, specifications, and plans
- **`legacy_docs/`** — Completed sprint reports, session logs, and superseded versions

---

## Active Documentation

### Architecture & Design

| Document | Description |
|----------|-------------|
| [AL-FURQAN-ARCHITECTURE-v3.0](active_docs/AL-FURQAN-ARCHITECTURE-v3.0.md) | Single source of truth — full system architecture (4 layers, gates, chains, Z3, security) |
| [AL-FURQAN-IMPLEMENTATION-PLAN-v1.0](active_docs/AL-FURQAN-IMPLEMENTATION-PLAN-v1.0.md) | Task-level breakdown for Sprints 3-6 (all completed) |
| [FURQAN-AXIOM-SECURITY-POLICY-v1.0](active_docs/FURQAN-AXIOM-SECURITY-POLICY-v1.0.md) | 5-layer security hardening specification |
| [the-criterion-formal-axioms.tex](active_docs/the-criterion-formal-axioms.tex) | Formal LaTeX axiom definitions |

### Knowledge Base & Data

| Document | Description |
|----------|-------------|
| [AL-FURQAN-KNOWLEDGE-GRAPH-DOCS](active_docs/AL-FURQAN-KNOWLEDGE-GRAPH-DOCS.md) | KB schema, edge types, collections (Quran, Hadith, Fiqh) |
| [ELASTICSEARCH-MIGRATION](active_docs/ELASTICSEARCH-MIGRATION.md) | Full migration from ChromaDB/JSON to Elasticsearch (completed Mar 30) |
| [KNOWLEDGE-GRAPH-LEARNING-PLAN-v1.0](active_docs/KNOWLEDGE-GRAPH-LEARNING-PLAN-v1.0.md) | LLM-assisted KB graph building for Surat Al-An'am |

### Tokenizer & Training

| Document | Description |
|----------|-------------|
| [QURAN-TOKENIZER-v1.0](active_docs/QURAN-TOKENIZER-v1.0.md) | 5-level tokenizer (Word, Root, Semantic, Logic, Transition) with reward signal formula |
| [FURQAN-TRAINING-PRD-v1.0](active_docs/FURQAN-TRAINING-PRD-v1.0.md) | PRD for training Furqan-27B on tokenized Quran data with Unsloth |
| [FURQAN-TRAINING-IMPLEMENTATION-PLAN-v1.0](active_docs/FURQAN-TRAINING-IMPLEMENTATION-PLAN-v1.0.md) | Technical blueprint: data prep, SFT, DPO, eval, deployment |
| [FINE-TUNING-IMPLEMENTATION-PLAN-v1.0](active_docs/FINE-TUNING-IMPLEMENTATION-PLAN-v1.0.md) | Earlier SFT + DPO plan (superseded by Training PRD/Plan above) |
| [RAG-IMPLEMENTATION-PLAN-v1.0](active_docs/RAG-IMPLEMENTATION-PLAN-v1.0.md) | Engine-guided RAG pipeline design (implemented, 100 tests) |

### MCP Skills

| Document | Description |
|----------|-------------|
| [FURQAN-RAAS-DOCS](active_docs/FURQAN-RAAS-DOCS.md) | Reasoning-as-a-Skill MCP server (5 tools, 31 tests) |
| [FURQAN-REASONING-AS-A-SKILL-v1.0](active_docs/FURQAN-REASONING-AS-A-SKILL-v1.0.md) | RaaS architecture specification |
| [FURQAN-MEMORY-DOCS](active_docs/FURQAN-MEMORY-DOCS.md) | Client-side Memory skill (SQLite + ChromaDB, 56 tests) |
| [FURQAN-MEMORY-SKILL-v1.0](active_docs/FURQAN-MEMORY-SKILL-v1.0.md) | Memory skill architecture specification |
| [FURQAN-SKILLS-IMPLEMENTATION-PLAN-v1.0](active_docs/FURQAN-SKILLS-IMPLEMENTATION-PLAN-v1.0.md) | Implementation roadmap for both skills |

### Project Status

| Document | Description |
|----------|-------------|
| [PROJECT-STATUS](active_docs/PROJECT-STATUS.md) | Current project state, what's done, what's planned |

---

## Legacy Documentation

Historical records from completed sprints and sessions. Preserved for audit trail.

| Document | Date | Description |
|----------|------|-------------|
| [AL-FURQAN-ARCHITECTURE-v2.0](legacy_docs/AL-FURQAN-ARCHITECTURE-v2.0.md) | Mar 20, 2026 | Superseded by v3.0 |
| [SPRINT-2-DOCUMENTATION](legacy_docs/SPRINT-2-DOCUMENTATION.md) | Mar 20, 2026 | Auth, security, testing infrastructure |
| [SPRINT-3-5-ENGINE-DOCS](legacy_docs/SPRINT-3-5-ENGINE-DOCS.md) | Mar 21, 2026 | Engine refactor, KB, gates, chains, Z3 |
| [SPRINT-6-SECURITY-DOCS](legacy_docs/SPRINT-6-SECURITY-DOCS.md) | Mar 21, 2026 | Security hardening (5 layers) |
| [SPRINT-REPORT-2026-03-22](legacy_docs/SPRINT-REPORT-2026-03-22.md) | Mar 22, 2026 | RAG pipeline sprint (100 tests) |
| [DAILY-REPORT-2026-03-21](legacy_docs/DAILY-REPORT-2026-03-21.md) | Mar 21, 2026 | Sprints 3-6 execution (647 tests) |
| [SESSION-REPORT-2026-03-19](legacy_docs/SESSION-REPORT-2026-03-19.md) | Mar 19, 2026 | First session — 44K documents integrated |
| [SESSION-REPORT-2026-03-29-30](legacy_docs/SESSION-REPORT-2026-03-29-30.md) | Mar 29-30, 2026 | ES migration, tokenizer, code quality |
| [LESSON-PIPELINE-REPORT-2026-03-29](legacy_docs/LESSON-PIPELINE-REPORT-2026-03-29.md) | Mar 29, 2026 | 3-stage pipeline, 2,487 training pairs |
| [LINTING-CHANGELOG](legacy_docs/LINTING-CHANGELOG.md) | Mar 29, 2026 | Pylint/ruff compliance audit trail |
