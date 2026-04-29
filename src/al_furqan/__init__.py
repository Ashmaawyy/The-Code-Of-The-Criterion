"""Al-Furqan (The Criterion) — Axiom-anchored reasoning engine."""

import logging

__version__ = "0.1.0"

LOG_FORMAT = "🕒 %(asctime)s - 📍 %(name)s - [%(levelname)s]  %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging once for the current process.

    Safe to call multiple times — ``basicConfig`` is a no-op after the first call.
    """
    logging.basicConfig(level=level, format=LOG_FORMAT, datefmt=LOG_DATEFMT)
