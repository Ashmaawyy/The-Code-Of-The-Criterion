"""Load the 'how people talk about history' testing JSONL into Neo4j.

Reads data_archive/training/testing/model_testing_how_people_talk_about_history.jsonl
and creates one Episode node per event (one event = one full-episode transcript):

    (:Episode {
        event_id, episode_slug, name, source, event_type, country, period,
        text, char_count
    })

Only touches Episode nodes on load — does NOT wipe the whole DB (unlike
load_neo4j.py which clears and rebuilds the Quran graph).

Usage:
    python scripts/rendering/load_testing_history_neo4j.py
    python scripts/rendering/load_testing_history_neo4j.py --neo4j-url bolt://localhost:7687
    python scripts/rendering/load_testing_history_neo4j.py --reset   # drop Episode nodes first
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from _neo4j import add_neo4j_arg, init_logging, neo4j_driver
from al_furqan.paths import TESTING_TALK_ABOUT_HISTORY_JSONL as DEFAULT_JSONL

logger = logging.getLogger(__name__)


def _reset(driver) -> None:
    with driver.session() as session:
        logger.info("Deleting existing Episode subgraph...")
        session.run("MATCH (e:Episode) DETACH DELETE e")


def _ensure_indexes(driver) -> None:
    with driver.session() as session:
        session.run("CREATE INDEX IF NOT EXISTS FOR (e:Episode) ON (e.event_id)")
        session.run("CREATE INDEX IF NOT EXISTS FOR (e:Episode) ON (e.episode_slug)")
        session.run("CREATE INDEX IF NOT EXISTS FOR (e:Episode) ON (e.source)")


def _load_jsonl(path: Path) -> list[dict]:
    episodes = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            edge_data = event["edges"][0]["data"]
            episodes.append({
                "event_id": event["event_id"],
                "episode_slug": edge_data.get("episode_slug", ""),
                "name": event.get("name", ""),
                "source": event.get("source", ""),
                "event_type": event.get("event_type", ""),
                "country": event.get("country", ""),
                "period": event.get("period", ""),
                "text": edge_data.get("text", ""),
                "char_count": edge_data.get("char_count", 0),
            })
    return episodes


def load(driver, jsonl_path: Path, reset: bool) -> None:
    if not jsonl_path.exists():
        raise SystemExit(f"JSONL not found: {jsonl_path}")

    if reset:
        _reset(driver)

    _ensure_indexes(driver)

    logger.info("Reading %s", jsonl_path)
    episodes = _load_jsonl(jsonl_path)
    logger.info("  %d episodes loaded", len(episodes))

    with driver.session() as session:
        for i in range(0, len(episodes), 200):
            batch = episodes[i:i + 200]
            session.run(
                """
                UNWIND $batch AS ep
                MERGE (e:Episode {event_id: ep.event_id})
                SET e.episode_slug = ep.episode_slug,
                    e.name = ep.name,
                    e.source = ep.source,
                    e.event_type = ep.event_type,
                    e.country = ep.country,
                    e.period = ep.period,
                    e.text = ep.text,
                    e.char_count = ep.char_count
                """,
                batch=batch,
            )
        logger.info("  Merged %d Episode nodes", len(episodes))

    with driver.session() as session:
        n = session.run("MATCH (e:Episode) RETURN count(e) AS c").single()["c"]
        logger.info("  Episode count in DB: %d", n)


def main() -> int:
    init_logging()
    parser = argparse.ArgumentParser(
        description="Load testing history JSONL into Neo4j (Episode subgraph)")
    add_neo4j_arg(parser)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--reset", action="store_true",
                        help="Delete existing Episode nodes before loading")
    args = parser.parse_args()

    with neo4j_driver(args.neo4j_url) as driver:
        load(driver, args.jsonl, reset=args.reset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
