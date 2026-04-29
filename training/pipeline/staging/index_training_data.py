"""Bulk-index training JSONL files into Elasticsearch.

Thin runner: reads the training index plan from
``al_furqan.kb.es.indices.TRAINING_INDEX_PLAN`` and bulk-loads each jsonl
into its target index. All mappings and plan entries live in the shared
``indices`` module so there is exactly one place where ES schemas are
defined in the project.

Usage:
    python -m training.pipeline.staging.index_training_data
    python -m training.pipeline.staging.index_training_data --only graph
    python -m training.pipeline.staging.index_training_data --force
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Iterator

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from al_furqan.kb.es.client import create_es_client
from al_furqan.kb.es.indices import TRAINING_INDEX_PLAN
from al_furqan.paths import DATA_TRAINING as DATA_DIR

logger = logging.getLogger(__name__)

BULK_BATCH_SIZE = 2000


# ---------------------------------------------------------------------------
# Action iterators
# ---------------------------------------------------------------------------

def _iter_graph_actions(path: Path, index: str) -> Iterator[dict]:
    """Flatten verse graph: one ES doc per edge."""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            node = json.loads(line)
            vk = node["verse_key"]
            base = {
                "verse_key": vk,
                "surah": node["surah"],
                "ayah": node["ayah"],
                "revelation_type": node.get("revelation_type", ""),
                "juz": node.get("juz"),
            }
            for edge in node.get("edges", []):
                doc = {**base}
                doc["edge_type"] = edge["edge_type"]
                doc["target_id"] = edge.get("target_id", "")
                doc["weight"] = edge.get("weight", 1.0)
                doc["confidence"] = edge.get("confidence", 1.0)
                doc["provenance"] = edge.get("provenance", "")
                data = edge.get("data", {})
                doc["tafsir_book"] = data.get("tafsir_book", "")
                doc["tafsir_scholar"] = data.get("tafsir_scholar", "")
                doc["tafsir_era"] = data.get("tafsir_era", "")
                doc["collection"] = data.get("collection", "")
                doc["event_id"] = data.get("event_id", "")
                doc["period"] = data.get("period", "")
                doc["transition_type"] = data.get("transition_type", "")
                doc["smoothness"] = data.get("smoothness")
                doc["lesson_number"] = data.get("lesson_number")
                doc["relation"] = data.get("relation", "")
                yield {"_index": index, "_source": doc}


def _iter_history_actions(path: Path, index: str) -> Iterator[dict]:
    """Index history events as-is (one doc per event)."""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            event = json.loads(line)
            event["edge_count"] = len(event.get("edges", []))
            yield {"_index": index, "_id": event.get("event_id", ""), "_source": event}


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def _ensure_index(es: Elasticsearch, name: str, mapping: dict, force: bool) -> None:
    if es.indices.exists(index=name):
        if force:
            logger.info("Dropping existing index: %s (--force)", name)
            es.indices.delete(index=name)
        else:
            logger.info("Index %s exists, will upsert", name)
            return
    logger.info("Creating index %s", name)
    es.indices.create(index=name, **mapping)


def run(es: Elasticsearch, only: list[str], dry_run: bool, force: bool = False) -> None:
    for key, plan in TRAINING_INDEX_PLAN.items():
        if only and key not in only:
            continue

        path = DATA_DIR / plan["file"]
        if not path.exists():
            logger.warning("Missing %s, skipping %s", path, key)
            continue

        logger.info("=" * 60)
        logger.info("Indexing %s -> %s", key, plan["index"])
        logger.info("=" * 60)

        if not dry_run:
            _ensure_index(es, plan["index"], plan["mapping"], force)

        if plan.get("flatten"):
            actions = _iter_graph_actions(path, plan["index"])
        else:
            actions = _iter_history_actions(path, plan["index"])

        if dry_run:
            count = sum(1 for _ in actions)
            logger.info("[dry-run] would index %d docs", count)
        else:
            success, errors = bulk(
                es, actions,
                chunk_size=BULK_BATCH_SIZE,
                raise_on_error=False,
                request_timeout=120,
            )
            if errors:
                logger.warning("  %d errors (first: %s)", len(errors), errors[0] if errors else "")
            es.indices.refresh(index=plan["index"])
            final = es.count(index=plan["index"])["count"]
            logger.info("  %s: indexed %d, final count %d", plan["index"], success, final)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Index training data into ES")
    parser.add_argument("--es-url", default=None)
    parser.add_argument("--only", nargs="*", default=[], choices=list(TRAINING_INDEX_PLAN.keys()))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Drop and recreate indices")
    args = parser.parse_args()

    hosts = [args.es_url] if args.es_url else None
    es = create_es_client(hosts=hosts)
    run(es, only=args.only, dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
