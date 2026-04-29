"""Load the verse-centric knowledge graph into Neo4j for visualization.

Creates Ayah nodes (6,236) and typed relationships to Tafsir, Hadith,
SiraEvent, Lesson nodes, plus direct Ayah→Ayah edges for transitions
and cross-references.

Usage:
    python scripts/rendering/load_neo4j.py
    python scripts/rendering/load_neo4j.py --neo4j-url bolt://localhost:7687
    python scripts/rendering/load_neo4j.py --graph-path data_archive/training/quran_graph.jsonl

Then open http://localhost:7474 to explore in Neo4j Browser.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from _neo4j import add_neo4j_arg, init_logging, neo4j_driver
from al_furqan.paths import QURAN_GRAPH_JSONL as DEFAULT_GRAPH

logger = logging.getLogger(__name__)


def load(driver, graph_path: Path) -> None:
    """Load the full graph into Neo4j."""

    with driver.session() as session:
        # Clear existing data
        logger.info("Clearing existing graph...")
        session.run("MATCH (n) DETACH DELETE n")

        # Create indexes for performance
        logger.info("Creating indexes...")
        session.run("CREATE INDEX IF NOT EXISTS FOR (a:Ayah) ON (a.verse_key)")
        session.run("CREATE INDEX IF NOT EXISTS FOR (a:Ayah) ON (a.surah)")
        session.run("CREATE INDEX IF NOT EXISTS FOR (t:Tafsir) ON (t.target_id)")
        session.run("CREATE INDEX IF NOT EXISTS FOR (h:Hadith) ON (h.target_id)")
        session.run("CREATE INDEX IF NOT EXISTS FOR (s:SiraEvent) ON (s.target_id)")
        session.run("CREATE INDEX IF NOT EXISTS FOR (l:Lesson) ON (l.target_id)")

    # Pass 1: Create all Ayah nodes
    logger.info("Loading ayah nodes from %s...", graph_path)
    ayah_batch = []
    all_edges = []

    with open(graph_path, encoding="utf-8") as f:
        for line in f:
            node = json.loads(line)
            ayah_batch.append({
                "verse_key": node["verse_key"],
                "surah": node["surah"],
                "ayah": node["ayah"],
                "text_ar": node.get("text_ar", "")[:200],
                "text_en": node.get("text_en", "")[:200],
                "revelation_type": node.get("revelation_type", ""),
                "juz": node.get("juz"),
                "total_edges": len(node.get("edges", [])),
            })
            for edge in node.get("edges", []):
                all_edges.append((node["verse_key"], edge))

    # Batch create ayah nodes
    with driver.session() as session:
        for i in range(0, len(ayah_batch), 500):
            batch = ayah_batch[i:i+500]
            session.run(
                """
                UNWIND $batch AS a
                CREATE (n:Ayah {
                    verse_key: a.verse_key,
                    surah: a.surah,
                    ayah: a.ayah,
                    text_ar: a.text_ar,
                    text_en: a.text_en,
                    revelation_type: a.revelation_type,
                    juz: a.juz,
                    total_edges: a.total_edges
                })
                """,
                batch=batch,
            )
        logger.info("Created %d Ayah nodes", len(ayah_batch))

    # Pass 2: Create edges by type
    # Group edges
    tafsir_edges = []
    hadith_edges = []
    sira_edges = []
    lesson_edges = []
    transition_edges = []
    crossref_edges = []

    for vk, edge in all_edges:
        et = edge.get("edge_type", "")
        data = edge.get("data", {})
        rec = {"from_vk": vk, "target_id": edge.get("target_id", ""), "weight": edge.get("weight", 1.0)}

        if et == "tafsir":
            rec["book"] = data.get("tafsir_book", "")[:60]
            rec["scholar"] = data.get("tafsir_scholar", "")
            rec["era"] = data.get("tafsir_era", "")
            tafsir_edges.append(rec)
        elif et == "hadith":
            rec["collection"] = data.get("collection", "")
            rec["number"] = data.get("number", "")
            rec["quote"] = data.get("matched_quote", "")[:100]
            hadith_edges.append(rec)
        elif et == "sira_event":
            rec["title_ar"] = data.get("title_ar", "")[:80]
            rec["title_en"] = data.get("title_en", "")[:80]
            rec["period"] = data.get("period", "")
            sira_edges.append(rec)
        elif et == "lesson":
            rec["lesson_num"] = data.get("lesson_number", 0)
            rec["chapter_title"] = data.get("chapter_title", "")[:60]
            lesson_edges.append(rec)
        elif et in ("next_ayah", "prev_ayah"):
            rec["direction"] = et
            rec["transition_type"] = data.get("transition_type", "")
            rec["smoothness"] = data.get("smoothness", 1.0)
            transition_edges.append(rec)
        elif et == "cross_ref":
            rec["relation"] = data.get("relation", "")
            crossref_edges.append(rec)

    with driver.session() as session:
        # Tafsir: create Tafsir nodes + relationships (sample — too many for full load)
        # Deduplicate tafsir by book name, create one node per book
        tafsir_books = {}
        for e in tafsir_edges:
            book = e["book"]
            if book not in tafsir_books:
                tafsir_books[book] = {"book": book, "scholar": e["scholar"], "era": e["era"]}

        session.run(
            "UNWIND $books AS b CREATE (:TafsirBook {name: b.book, scholar: b.scholar, era: b.era})",
            books=list(tafsir_books.values()),
        )
        logger.info("Created %d TafsirBook nodes", len(tafsir_books))

        # Tafsir edges (batch)
        for i in range(0, len(tafsir_edges), 2000):
            batch = tafsir_edges[i:i+2000]
            session.run(
                """
                UNWIND $batch AS e
                MATCH (a:Ayah {verse_key: e.from_vk})
                MATCH (t:TafsirBook {name: e.book})
                CREATE (a)-[:HAS_TAFSIR {weight: e.weight}]->(t)
                """,
                batch=batch,
            )
        logger.info("Created %d tafsir edges", len(tafsir_edges))

        # Hadith nodes + edges
        hadith_nodes = {}
        for e in hadith_edges:
            tid = e["target_id"]
            if tid not in hadith_nodes:
                hadith_nodes[tid] = {
                    "target_id": tid,
                    "collection": e["collection"],
                    "number": e["number"],
                }
        if hadith_nodes:
            session.run(
                "UNWIND $nodes AS h CREATE (:Hadith {target_id: h.target_id, collection: h.collection, number: h.number})",
                nodes=list(hadith_nodes.values()),
            )
            for i in range(0, len(hadith_edges), 1000):
                batch = hadith_edges[i:i+1000]
                session.run(
                    """
                    UNWIND $batch AS e
                    MATCH (a:Ayah {verse_key: e.from_vk})
                    MATCH (h:Hadith {target_id: e.target_id})
                    CREATE (a)-[:QUOTED_IN {weight: e.weight, quote: e.quote}]->(h)
                    """,
                    batch=batch,
                )
            logger.info("Created %d hadith nodes, %d edges", len(hadith_nodes), len(hadith_edges))

        # Sira nodes + edges
        sira_nodes = {}
        for e in sira_edges:
            tid = e["target_id"]
            if tid not in sira_nodes:
                sira_nodes[tid] = {
                    "target_id": tid,
                    "title_ar": e["title_ar"],
                    "title_en": e["title_en"],
                    "period": e["period"],
                }
        if sira_nodes:
            session.run(
                "UNWIND $nodes AS s CREATE (:SiraEvent {target_id: s.target_id, title_ar: s.title_ar, title_en: s.title_en, period: s.period})",
                nodes=list(sira_nodes.values()),
            )
            for i in range(0, len(sira_edges), 1000):
                batch = sira_edges[i:i+1000]
                session.run(
                    """
                    UNWIND $batch AS e
                    MATCH (a:Ayah {verse_key: e.from_vk})
                    MATCH (s:SiraEvent {target_id: e.target_id})
                    CREATE (a)-[:REVEALED_FOR {weight: e.weight}]->(s)
                    """,
                    batch=batch,
                )
            logger.info("Created %d sira nodes, %d edges", len(sira_nodes), len(sira_edges))

        # Lesson nodes + edges
        lesson_nodes = {}
        for e in lesson_edges:
            tid = e["target_id"]
            if tid not in lesson_nodes:
                lesson_nodes[tid] = {
                    "target_id": tid,
                    "lesson_num": e["lesson_num"],
                    "chapter_title": e["chapter_title"],
                }
        if lesson_nodes:
            session.run(
                "UNWIND $nodes AS l CREATE (:Lesson {target_id: l.target_id, lesson_num: l.lesson_num, chapter_title: l.chapter_title})",
                nodes=list(lesson_nodes.values()),
            )
            for i in range(0, len(lesson_edges), 1000):
                batch = lesson_edges[i:i+1000]
                session.run(
                    """
                    UNWIND $batch AS e
                    MATCH (a:Ayah {verse_key: e.from_vk})
                    MATCH (l:Lesson {target_id: e.target_id})
                    CREATE (a)-[:TAUGHT_IN {weight: e.weight}]->(l)
                    """,
                    batch=batch,
                )
            logger.info("Created %d lesson nodes, %d edges", len(lesson_nodes), len(lesson_edges))

        # Ayah→Ayah transitions (next/prev)
        for i in range(0, len(transition_edges), 2000):
            batch = transition_edges[i:i+2000]
            session.run(
                """
                UNWIND $batch AS e
                MATCH (a:Ayah {verse_key: e.from_vk})
                MATCH (b:Ayah {verse_key: e.target_id})
                CREATE (a)-[:FLOWS_TO {
                    direction: e.direction,
                    transition_type: e.transition_type,
                    smoothness: e.smoothness
                }]->(b)
                """,
                batch=batch,
            )
        logger.info("Created %d transition edges", len(transition_edges))

        # Ayah→Ayah cross-references
        for i in range(0, len(crossref_edges), 1000):
            batch = crossref_edges[i:i+1000]
            session.run(
                """
                UNWIND $batch AS e
                MATCH (a:Ayah {verse_key: e.from_vk})
                MATCH (b:Ayah {verse_key: e.target_id})
                CREATE (a)-[:CROSS_REF {relation: e.relation, weight: e.weight}]->(b)
                """,
                batch=batch,
            )
        logger.info("Created %d cross-ref edges", len(crossref_edges))

    # Final stats
    with driver.session() as session:
        result = session.run(
            "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY cnt DESC"
        )
        logger.info("=== Neo4j Node Counts ===")
        for record in result:
            logger.info("  %-15s %8d", record["label"], record["cnt"])

        result = session.run(
            "MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS cnt ORDER BY cnt DESC"
        )
        logger.info("=== Neo4j Relationship Counts ===")
        for record in result:
            logger.info("  %-15s %8d", record["rel"], record["cnt"])


def main():
    init_logging()

    parser = argparse.ArgumentParser(description="Load verse graph into Neo4j")
    add_neo4j_arg(parser)
    parser.add_argument("--graph-path", type=Path, default=DEFAULT_GRAPH)
    args = parser.parse_args()

    with neo4j_driver(args.neo4j_url) as driver:
        load(driver, args.graph_path)


if __name__ == "__main__":
    main()
