"""Generate vector embeddings and store in Elasticsearch dense_vector fields.

Reads documents from ES indices, generates embeddings via the EmbeddingModel,
and writes them back as dense_vector field updates.

Usage:
    python -m al_furqan.kb.es.migrate_embeddings                   # all indices
    python -m al_furqan.kb.es.migrate_embeddings --index quran     # one index
    python -m al_furqan.kb.es.migrate_embeddings --dry-run         # preview
"""

import argparse
import logging
import time

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from al_furqan import setup_logging
from al_furqan.kb.es.client import create_es_client

logger = logging.getLogger(__name__)

# Embedding text templates — must match what QuranCollection / HadithCollection use
# so that vector similarity is consistent.
QURAN_EMBED_TEMPLATE = "{text_ar} {text_en}"
HADITH_EMBED_TEMPLATE = "{text_ar} {text_en}"
VERDICT_EMBED_TEMPLATE = (
    "Question: {question}\n"
    "System: {primary_system}\n"
    "Friction Points: {friction_points}\n"
    "Reasoning: {revised_reasoning}\n"
    "Judgment: {final_judgment}"
)


# ---------------------------------------------------------------------------
# Generate mode: create fresh embeddings from source text in ES
# ---------------------------------------------------------------------------


def _generate_for_index(
    es: Elasticsearch,
    embed_fn,
    index_name: str,
    text_builder,
    batch_size: int = 200,
    dry_run: bool = False,
) -> int:
    """Generate embeddings for all docs in an index and update them.

    Args:
        es: Elasticsearch client.
        embed_fn: callable(list[str]) -> list[list[float]]
        index_name: ES index to update.
        text_builder: callable(doc_source) -> str that builds the text to embed.
        batch_size: number of docs to process at once.
        dry_run: if True, count only.

    Returns:
        Number of documents updated.
    """
    if not es.indices.exists(index=index_name):
        logger.warning("Index %s does not exist, skipping", index_name)
        return 0

    # Count total docs
    total = es.count(index=index_name)["count"]
    if total == 0:
        logger.info("Index %s is empty, nothing to embed", index_name)
        return 0

    if dry_run:
        logger.info(
            "[DRY RUN] Would generate embeddings for %d docs in %s", total, index_name
        )
        return total

    logger.info("Generating embeddings for %d docs in %s...", total, index_name)
    start = time.monotonic()
    updated = 0

    # Scroll through all documents
    resp = es.search(
        index=index_name,
        body={"query": {"match_all": {}}, "size": batch_size},
        scroll="5m",
    )
    scroll_id = resp["_scroll_id"]

    while True:
        hits = resp["hits"]["hits"]
        if not hits:
            break

        # Build texts for embedding
        texts = []
        doc_ids = []
        for hit in hits:
            text = text_builder(hit["_source"])
            if text:
                texts.append(text)
                doc_ids.append(hit["_id"])

        if texts:
            # Generate embeddings in batch
            embeddings = embed_fn(texts)

            # Build bulk update actions
            actions = []
            for doc_id, embedding in zip(doc_ids, embeddings):
                actions.append(
                    {
                        "_op_type": "update",
                        "_index": index_name,
                        "_id": doc_id,
                        "doc": {"embedding": embedding},
                    }
                )

            success, errors = bulk(es, actions, raise_on_error=False)
            if errors:
                logger.warning("%d update errors in batch", len(errors))
            updated += success

        # Next scroll page
        resp = es.scroll(scroll_id=scroll_id, scroll="5m")

    es.clear_scroll(scroll_id=scroll_id)
    elapsed = time.monotonic() - start
    logger.info(
        "Generated embeddings for %d/%d docs in %s (%.1fs)",
        updated,
        total,
        index_name,
        elapsed,
    )
    return updated


def _quran_text_builder(source: dict) -> str:
    return QURAN_EMBED_TEMPLATE.format(
        text_ar=source.get("text_ar", ""),
        text_en=source.get("text_en", ""),
    )


def _hadith_text_builder(source: dict) -> str:
    return HADITH_EMBED_TEMPLATE.format(
        text_ar=source.get("text_ar", ""),
        text_en=source.get("text_en", ""),
    )


def _verdict_text_builder(source: dict) -> str:
    fps = source.get("friction_points", [])
    if isinstance(fps, list):
        fps = "; ".join(fps)
    return VERDICT_EMBED_TEMPLATE.format(
        question=source.get("question", ""),
        primary_system=source.get("primary_system", ""),
        friction_points=fps,
        revised_reasoning=source.get("revised_reasoning", ""),
        final_judgment=source.get("final_judgment", ""),
    )


# Index → text builder mapping
_INDEX_TEXT_BUILDERS = {
    "quran": _quran_text_builder,
    "hadith": _hadith_text_builder,
    "verdicts": _verdict_text_builder,
}


def generate_embeddings(
    es: Elasticsearch,
    embed_fn,
    prefix: str = "furqan",
    only: list[str] | None = None,
    batch_size: int = 200,
    dry_run: bool = False,
) -> dict[str, int]:
    """Generate embeddings for all supported indices.

    Args:
        es: Elasticsearch client.
        embed_fn: callable(list[str]) -> list[list[float]]
        prefix: Index name prefix.
        only: Specific indices to process (default: all supported).
        batch_size: Docs per batch.
        dry_run: Preview mode.

    Returns:
        {index_suffix: docs_updated}
    """
    targets = only or list(_INDEX_TEXT_BUILDERS.keys())
    results = {}

    for name in targets:
        if name not in _INDEX_TEXT_BUILDERS:
            logger.warning(
                "No text builder for index '%s', skipping (supported: %s)",
                name,
                list(_INDEX_TEXT_BUILDERS.keys()),
            )
            continue

        index_name = f"{prefix}_{name}"
        count = _generate_for_index(
            es,
            embed_fn,
            index_name,
            _INDEX_TEXT_BUILDERS[name],
            batch_size=batch_size,
            dry_run=dry_run,
        )
        results[name] = count

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    """Entry point."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Generate vector embeddings and store in Elasticsearch dense_vector fields"
    )
    parser.add_argument(
        "--index",
        nargs="*",
        default=None,
        choices=list(_INDEX_TEXT_BUILDERS.keys()),
        help="Process specific indices (default: all)",
    )
    parser.add_argument(
        "--model", default="minilm", help="Embedding model name (default: minilm)"
    )
    parser.add_argument(
        "--batch-size", type=int, default=200, help="Documents per batch (default: 200)"
    )
    parser.add_argument(
        "--prefix", default="furqan", help="Index name prefix (default: furqan)"
    )
    parser.add_argument("--es-url", default=None, help="Elasticsearch URL")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without writing"
    )
    args = parser.parse_args()

    hosts = [args.es_url] if args.es_url else None
    es = create_es_client(hosts=hosts)

    logger.info("Loading embedding model: %s", args.model)
    from al_furqan.kb.embeddings import EmbeddingModel

    model = EmbeddingModel(args.model)
    logger.info("Model loaded (dimension=%d)", model.dimension)

    results = generate_embeddings(
        es,
        embed_fn=model.embed,
        prefix=args.prefix,
        only=args.index,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )

    total = sum(results.values())
    logger.info("Embedding migration complete: %d total documents", total)
    for name, count in results.items():
        logger.info("  %-12s %d documents", name, count)


if __name__ == "__main__":
    main()
