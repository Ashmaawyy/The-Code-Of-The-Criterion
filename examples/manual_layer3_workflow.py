"""
Manual Layer‑3 Workflow — Master Ingestion Script

Phases implemented:
- Phase 1 (Environment): instructions to install dependencies
- Phase 2 (Master ingestion): build 'Knowledge Packages' (scholarly grading + tafsir)
- Phase 3 (Criterion retrieval): query the Knowledge-packages collection and show how
  to surface evidence for the Criterion reasoning pipeline

Usage (recommended):
    pip install -r requirements.txt
    python examples/manual_layer3_workflow.py --build
    python examples/manual_layer3_workflow.py --query "intention hadith bukhari"

Notes:
- This script uses `evaluation.vectordb.VectorDBBuilder.build_knowledge_packages_collection`
  (which creates the `sharia_knowledge` collection). If you don't have Chroma/embeddings
  installed, the script will still run in fallback mode but indexing will be limited.
"""
from pathlib import Path
import json

from evaluation.vectordb import VectorDBBuilder, build_sharia_knowledge_packages, query_sharia_knowledge
from evaluation.pipeline import CriterionPipeline


def phase_1_environment_setup():
    print("\nPHASE 1: Environment setup — run these in your terminal (Conda/Pip active):\n")
    print("  pip install -r requirements.txt\n  # (recommended) pip install chromadb sentence-transformers torch\n")


def phase_2_master_ingest(persist_dir: str = './.chromadb'):
    print("\nPHASE 2: Master ingestion — building Knowledge Packages into Chroma\n")
    builder = VectorDBBuilder(persist_directory=persist_dir)

    print("  -> Building 'sharia_knowledge' collection (this may take a few minutes)")
    info = build_sharia_knowledge_packages(corpus_folder='vectordb', persist_directory=persist_dir)
    print('\nBuild summary:')
    print(json.dumps(info, indent=2))
    print('\nThe knowledge-packages JSON is saved to vectordb/knowledge_packages.json for audit.')
    return builder


def phase_3_criterion_retrieval(builder: VectorDBBuilder, query: str):
    print("\nPHASE 3: Criterion retrieval & testing\n")
    print(f"Querying knowledge-packages for: {query}\n")

    hits = builder.query(query, collection_name='sharia_knowledge', k=6)
    for i, h in enumerate(hits['results']):
        kp = h['metadata'].get('knowledge_package', {})
        print(f"[{i+1}] distance={h['distance']:.4f} source={h['metadata'].get('source_file')}")
        if kp.get('canonical_id'):
            print(f"    canonical_id: {kp.get('canonical_id')}")
        print(f"    integrity_score: {kp.get('source_integrity_score')}")
        print(f"    scholarly_grade: {kp.get('scholarly_grading')}")
        snippet = h['document'][:400].replace('\n', ' ')
        print(f"    snippet: {snippet}...")
        print('-' * 60)

    # Show how to surface top evidence into Criterion reasoning (manual integration)
    # attach top-3 hit objects (metadata includes `knowledge_package`) so the pipeline
    # can boost Source-Integrity using `source_integrity_score` where available
    top_hits = hits['results'][:3]

    print('\n--- Example: using retrieved evidence inside the Criterion pipeline (manual) ---')
    pipeline = CriterionPipeline()
    sample_query = query

    # create a minimal system_data indicating no obvious axiom-violations (for demo)
    system_data = {
        'permits_exploitative_gain': False,
        'acknowledges_transcendent_source': False,
        'enables_accountability': True,
        'causes_harm_amplification': False,
        'destabilizes_lineage': False
    }

    # attach retrieved evidence (full hit objects) so gates can inspect `knowledge_package` metadata
    system_data['retrieved_evidence'] = {'hits': top_hits}

    print('\nRunning Criterion reasoning engine with attached evidence (for transparency)')
    result = pipeline.evaluate(sample_query, system_data)
    print('\nPhase 3 verdict summary:')
    print(json.dumps(result['phase_6_verdict'], indent=2))
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Manual Layer-3 ingestion + test workflow')
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--query', type=str, default=None)
    args = parser.parse_args()

    phase_1_environment_setup()

    builder = None
    if args.build:
        builder = phase_2_master_ingest()

    if args.query:
        if not builder:
            # lazy builder for queries
            builder = VectorDBBuilder()
        phase_3_criterion_retrieval(builder, args.query)


if __name__ == '__main__':
    main()
