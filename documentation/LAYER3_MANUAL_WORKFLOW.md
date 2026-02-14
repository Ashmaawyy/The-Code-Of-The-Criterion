# Layer‑3 Manual Architecture Workflow — Knowledge Packages

This document implements the **Manual Architecture Workflow** for Layer‑3:
we ingest scholarly texts (Hadith collections, Quran text), enrich them with
"Knowledge Packages" (scholarly grading + tafsir/exegesis + citation), store
these packages in ChromaDB, and expose them to The Criterion pipeline for
source-integrity checks and evidence-backed reasoning.

Why Knowledge Packages
- The Source-Integrity Gate (Layer 4) requires verifiable, graded sources.
- A "Knowledge Package" bundles: text chunk + canonical id + scholarly grading + tafsir + citation.
- This enables the pipeline to return traceable, citable evidence alongside verdicts.

Phase 1 — Environment Setup (local)
1. Activate your Python environment (Conda/venv)
2. Install dependencies:
   - pip install -r requirements.txt
   - Recommended extras: chromadb, sentence-transformers, torch

Phase 2 — Master Ingestion Script
- Script: `examples/manual_layer3_workflow.py`
- What it does:
  1. Parses all files in `vectordb/` (JSON, CSV, plain text, optional SQLite)
  2. Normalizes canonical identifiers (hadith numbers, Quran sura:ayah)
  3. Heuristically extracts scholarly grading (sahih/hasan/daif/unknown)
  4. Detects tafsir/exegesis where present in metadata
  5. Produces `knowledge_package` metadata and stores chunks in Chroma `sharia_knowledge` collection
  6. Optionally writes `vectordb/knowledge_packages.json` for auditing

Usage:
- Build the knowledge-packages collection:
    python examples/manual_layer3_workflow.py --build

- Query for evidence and test Criterion retrieval:
    python examples/manual_layer3_workflow.py --query "intention hadith bukhari"

Phase 3 — The "Criterion" Retrieval (Testing)
- Use `evaluation.vectordb` API (convenience wrappers):
  - `build_sharia_knowledge_packages()`  # one-shot build
  - `query_sharia_knowledge(query, k=5)`  # quick retrieval
- Example: call `CriterionPipeline().search_vectordb(query)` to get top evidence
  and include it in `system_data['retrieved_evidence']` before running `evaluate()`.

Integration points with The Criterion
- `knowledge_package['source_integrity_score']` is now consumed by the
  `Source-Integrity` gate: the engine will boost Source-Integrity when
  retrieved evidence contains high-integrity knowledge-packages.
- `canonical_id` and `citation` allow the pipeline to include verifiable
  citations in the final verdict and CoT scaffold.

Implementation note: `CriterionReasoningEngine.apply_gates()` inspects
`system_data['retrieved_evidence']['hits']` (if provided) and averages
`source_integrity_score` values to apply an evidence-based boost to the
Source-Integrity gate.

Files involved
- `evaluation/vectordb.py` — added `build_knowledge_packages_collection()` and helpers
- `examples/manual_layer3_workflow.py` — master ingestion + test workflow
- `documentation/LAYER3_MANUAL_WORKFLOW.md` — this file
- `vectordb/knowledge_packages.json` (generated) — audit log of knowledge packages

Operational guidance
- Re-run the build when source files change.
- Use `k=5..20` for retrieval during reasoning to get robust evidence.
- Extend `_extract_scholarly_grading` heuristics as you add new corpus metadata.

Next steps (recommendations)
- Add official tafsir sources and map them to Quran references (sura:ayah → tafsir text)
- Improve grading extraction by mapping known grading schemas to a canonical list
- Use `knowledge_package.source_integrity_score` inside `source_integrity_gate` for automated weighting

"Result: Layer‑3 now provides not just text, but traceable, graded knowledge — so The Criterion
can reason with evidence, cite sources, and apply its Source‑Integrity Gate reliably." 🔍
