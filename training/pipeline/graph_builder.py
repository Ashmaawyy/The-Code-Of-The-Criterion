"""Build the verse-centric knowledge graph by merging all edge extractors.

Each of 6,236 Quran verses becomes a central node with edges to tafsir,
adjacent verses, sira events, teacher lessons, cross-references, and hadith.

Output: data/training/quran_graph.jsonl — one JSON line per verse, sorted
by surah then ayah.

Usage:
    python -m training.pipeline.graph_builder
    python -m training.pipeline.graph_builder --extractors tafsir,sira
    python -m training.pipeline.graph_builder --output custom_path.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from pathlib import Path

from training.pipeline.extractors import ALL_EXTRACTORS
from training.pipeline.extractors.base import DATA_DIR, load_quran_map

logger = logging.getLogger(__name__)

OUTPUT_PATH = DATA_DIR / "training" / "quran_graph.jsonl"


def build(
    extractors: list[str] | None = None,
    output: Path = OUTPUT_PATH,
    es=None,
) -> Path:
    """Run extractors and merge into a single verse-centric JSONL."""

    quran = load_quran_map()
    logger.info("Loaded %d Quran verses", len(quran))

    # Initialize all verse nodes
    graph: dict[str, dict] = {}
    for vk, v in quran.items():
        graph[vk] = {
            "verse_key": vk,
            "surah": v["surah"],
            "ayah": v["ayah"],
            "text_ar": v.get("text_ar", ""),
            "text_en": v.get("text_en", ""),
            "revelation_type": v.get("revelation_type", ""),
            "juz": v.get("juz"),
            "page": v.get("page"),
            "edges": [],
            "edge_counts": {},
        }

    # Run each extractor and merge
    targets = extractors or list(ALL_EXTRACTORS.keys())
    total_edges = 0
    type_totals: Counter = Counter()

    for name in targets:
        if name not in ALL_EXTRACTORS:
            logger.warning("Unknown extractor: %s", name)
            continue

        logger.info("Running extractor: %s", name)
        extract_fn = ALL_EXTRACTORS[name]

        kwargs = {}
        if es is not None:
            kwargs["es"] = es

        edges_by_verse = extract_fn(**kwargs)

        # Merge into graph
        extractor_count = 0
        for vk, edges in edges_by_verse.items():
            if vk not in graph:
                # Verse key from extractor not in quran — warn and skip
                logger.debug("Unknown verse_key from %s: %s", name, vk)
                continue
            graph[vk]["edges"].extend(edges)
            extractor_count += len(edges)

        total_edges += extractor_count
        type_totals[name] = extractor_count
        logger.info("  %s: %d edges merged", name, extractor_count)

    # Compute per-verse edge_counts
    for node in graph.values():
        counts: Counter = Counter()
        for edge in node["edges"]:
            counts[edge["edge_type"]] += 1
        node["edge_counts"] = dict(counts)

    # Write output sorted by surah:ayah
    output.parent.mkdir(parents=True, exist_ok=True)
    sorted_keys = sorted(graph.keys(), key=lambda k: (graph[k]["surah"], graph[k]["ayah"]))

    with output.open("w", encoding="utf-8") as f:
        for vk in sorted_keys:
            f.write(json.dumps(graph[vk], ensure_ascii=False) + "\n")

    # Stats
    verses_with_edges = sum(1 for vk in graph if graph[vk]["edges"])
    verses_no_edges = len(graph) - verses_with_edges
    max_edges = max((len(n["edges"]) for n in graph.values()), default=0)
    avg_edges = total_edges / len(graph) if graph else 0

    logger.info("=" * 60)
    logger.info("Graph build complete: %s", output)
    logger.info("  Verses: %d total, %d with edges, %d without",
                len(graph), verses_with_edges, verses_no_edges)
    logger.info("  Edges: %d total (avg %.1f/verse, max %d)", total_edges, avg_edges, max_edges)
    for name, count in type_totals.most_common():
        logger.info("    %-15s %8d", name, count)
    logger.info("=" * 60)

    return output


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(
        description="Build verse-centric knowledge graph from all edge extractors")
    parser.add_argument("--extractors", default=None,
                        help="Comma-separated list of extractors (default: all)")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH,
                        help=f"Output path (default: {OUTPUT_PATH})")
    parser.add_argument("--es-url", default=None,
                        help="Elasticsearch URL")
    args = parser.parse_args()

    es = None
    if args.es_url:
        from al_furqan.kb.es.client import create_es_client
        es = create_es_client(hosts=[args.es_url])

    extractors = args.extractors.split(",") if args.extractors else None
    build(extractors=extractors, output=args.output, es=es)


if __name__ == "__main__":
    main()
