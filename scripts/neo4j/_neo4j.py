"""Shared Neo4j driver helpers for the rendering loaders.

Both `load_neo4j.py` (full Quran graph) and `load_testing_history_neo4j.py`
(Episode subgraph) need the same driver boilerplate: bolt URL flag, verified
connection, clean close. Each loader still owns its own schema, indexes,
and Cypher batches.
"""

from __future__ import annotations

import argparse
import logging
from contextlib import contextmanager
from typing import Iterator

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

DEFAULT_NEO4J_URL = "bolt://localhost:7687"


def add_neo4j_arg(parser: argparse.ArgumentParser) -> None:
    """Add the standard ``--neo4j-url`` flag to a loader's argparse."""
    parser.add_argument(
        "--neo4j-url",
        default=DEFAULT_NEO4J_URL,
        help=f"Neo4j bolt URL (default: {DEFAULT_NEO4J_URL})",
    )


@contextmanager
def neo4j_driver(url: str) -> Iterator:
    """Open, verify, and always close a Neo4j driver."""
    driver = GraphDatabase.driver(url, auth=None)
    try:
        driver.verify_connectivity()
        logger.info("Connected to Neo4j at %s", url)
        yield driver
    finally:
        driver.close()


def init_logging() -> None:
    """Set up the stdout logging the loaders expect."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
