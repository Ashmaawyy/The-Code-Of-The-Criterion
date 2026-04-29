"""Phase 3: Migrate verdicts and human feedback from JSON files into Elasticsearch.

Scans the verdicts directory and feedback directory for JSON files and
bulk-indexes them into the furqan_verdicts and furqan_feedback indices.

Usage:
    python -m al_furqan.kb.es.migrate_verdicts                       # migrate all
    python -m al_furqan.kb.es.migrate_verdicts --verdicts-dir DIR     # custom path
    python -m al_furqan.kb.es.migrate_verdicts --dry-run              # preview
    python -m al_furqan.kb.es.migrate_verdicts --verify               # verify counts
"""

import argparse
import json
import logging
import time
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError

from al_furqan import setup_logging
from al_furqan.kb.es.client import create_es_client
from al_furqan.paths import DATA_FEEDBACK

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Verdict loader
# ---------------------------------------------------------------------------

def _load_verdicts(verdicts_dir: Path, prefix: str):
    """Yield bulk actions for verdict JSON files.

    Each verdict file is a self-contained JSON object written by
    VerdictStore.store(). The file name (minus .json) is the verdict_id.

    Expected fields from Verdict.to_dict() + store metadata:
        question, primary_system, friction_points, gate_scores,
        origin_gate, revised_reasoning, final_judgment, total_score,
        passes, timestamp, status, id
    """
    if not verdicts_dir.exists():
        logger.warning("Verdicts directory does not exist: %s", verdicts_dir)
        return

    index = f"{prefix}_verdicts"
    files = sorted(verdicts_dir.glob("*.json"))
    if not files:
        logger.info("No verdict files found in %s", verdicts_dir)
        return

    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Skipping malformed verdict file %s: %s", path.name, exc)
            continue

        verdict_id = data.get("id", path.stem)

        # Map gate_scores from list of dicts to nested ES structure
        gate_scores = []
        for gs in data.get("gate_scores", []):
            gate_scores.append({
                "gate_id": gs.get("name", ""),
                "score": gs.get("score", 0),
                "reasoning": gs.get("reasoning", ""),
            })

        doc = {
            "verdict_id": verdict_id,
            "question": data.get("question", ""),
            "primary_system": data.get("primary_system", ""),
            "origin_gate": data.get("origin_gate", ""),
            "friction_points": data.get("friction_points", []),
            "revised_reasoning": data.get("revised_reasoning", ""),
            "final_judgment": data.get("final_judgment", ""),
            "total_score": data.get("total_score", 0),
            "passes": data.get("passes", False),
            "status": data.get("status", "unknown"),
            "timestamp": _to_epoch_millis(data.get("timestamp")),
            "gate_scores": gate_scores,
        }

        yield {"_index": index, "_id": verdict_id, "_source": doc}


# ---------------------------------------------------------------------------
# Feedback loader
# ---------------------------------------------------------------------------

def _load_feedback(feedback_dir: Path, prefix: str):
    """Yield bulk actions for feedback JSON files.

    Each feedback file is written by FeedbackStore.submit().
    Expected fields from HumanFeedback.to_dict() + feedback_id.
    """
    if not feedback_dir.exists():
        logger.warning("Feedback directory does not exist: %s", feedback_dir)
        return

    index = f"{prefix}_feedback"
    files = sorted(feedback_dir.glob("*.json"))
    if not files:
        logger.info("No feedback files found in %s", feedback_dir)
        return

    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Skipping malformed feedback file %s: %s", path.name, exc)
            continue

        feedback_id = data.get("feedback_id", path.stem)

        doc = {
            "feedback_id": feedback_id,
            "verdict_id": data.get("verdict_id", ""),
            "reviewer": data.get("reviewer", ""),
            "rating": data.get("rating", ""),
            "gate_corrections": data.get("gate_corrections", {}),
            "notes": data.get("notes", ""),
            "timestamp": _to_epoch_millis(data.get("timestamp")),
        }

        yield {"_index": index, "_id": feedback_id, "_source": doc}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_epoch_millis(ts) -> int | None:
    """Convert a timestamp (float seconds or None) to epoch milliseconds for ES."""
    if ts is None:
        return None
    try:
        return int(float(ts) * 1000)
    except (TypeError, ValueError):
        return None


def _bulk_index(es: Elasticsearch, actions: list, index_name: str,
                dry_run: bool = False) -> int:
    """Bulk-index a list of actions. Returns count of indexed docs."""
    if not actions:
        logger.info("No documents to index for %s", index_name)
        return 0

    if dry_run:
        logger.info("[DRY RUN] Would index %d documents into %s",
                    len(actions), index_name)
        return len(actions)

    logger.info("Indexing %d documents into %s...", len(actions), index_name)
    start = time.monotonic()

    try:
        success, errors = bulk(es, actions, raise_on_error=False)
        elapsed = time.monotonic() - start

        if errors:
            logger.error("%d indexing errors in %s:", len(errors), index_name)
            for err in errors[:5]:
                logger.error("  %s", err)

        logger.info("Indexed %d documents into %s in %.2fs",
                    success, index_name, elapsed)
        es.indices.refresh(index=index_name)
        return success

    except BulkIndexError as exc:
        logger.error("Bulk indexing failed for %s: %s", index_name, exc)
        return 0


# ---------------------------------------------------------------------------
# Main migration
# ---------------------------------------------------------------------------

def migrate_verdicts(
    es: Elasticsearch,
    verdicts_dir: Path,
    prefix: str = "furqan",
    dry_run: bool = False,
) -> int:
    """Migrate verdict JSON files to Elasticsearch."""
    index_name = f"{prefix}_verdicts"
    if not dry_run and not es.indices.exists(index=index_name):
        logger.error("Index %s does not exist. Run setup_indices first.", index_name)
        return 0

    actions = list(_load_verdicts(verdicts_dir, prefix))
    return _bulk_index(es, actions, index_name, dry_run=dry_run)


def migrate_feedback(
    es: Elasticsearch,
    feedback_dir: Path,
    prefix: str = "furqan",
    dry_run: bool = False,
) -> int:
    """Migrate feedback JSON files to Elasticsearch."""
    index_name = f"{prefix}_feedback"
    if not dry_run and not es.indices.exists(index=index_name):
        logger.error("Index %s does not exist. Run setup_indices first.", index_name)
        return 0

    actions = list(_load_feedback(feedback_dir, prefix))
    return _bulk_index(es, actions, index_name, dry_run=dry_run)


def verify_counts(
    es: Elasticsearch,
    verdicts_dir: Path,
    feedback_dir: Path,
    prefix: str = "furqan",
) -> bool:
    """Verify indexed counts match source file counts."""
    all_match = True

    for name, directory in [("verdicts", verdicts_dir), ("feedback", feedback_dir)]:
        index_name = f"{prefix}_{name}"
        expected = len(list(directory.glob("*.json"))) if directory.exists() else 0

        if not es.indices.exists(index=index_name):
            if expected > 0:
                logger.error("Index %s does not exist but %d source files found",
                             index_name, expected)
                all_match = False
            continue

        actual = es.count(index=index_name)["count"]
        status = "OK" if actual == expected else "MISMATCH"
        log_fn = logger.info if status == "OK" else logger.error
        log_fn("  %-20s expected=%d  actual=%d  [%s]",
               name, expected, actual, status)
        if actual != expected:
            all_match = False

    return all_match


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Entry point."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Migrate verdicts and feedback from JSON files into Elasticsearch")
    parser.add_argument("--verdicts-dir", type=Path, default=None,
                        help="Path to verdicts directory (default: from config)")
    parser.add_argument("--feedback-dir", type=Path, default=None,
                        help="Path to feedback directory (default: data/feedback)")
    parser.add_argument("--prefix", default="furqan",
                        help="Index name prefix (default: furqan)")
    parser.add_argument("--es-url", default=None,
                        help="Elasticsearch URL")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would be indexed without writing")
    parser.add_argument("--verify", action="store_true",
                        help="Verify document counts after migration")
    args = parser.parse_args()

    hosts = [args.es_url] if args.es_url else None
    es = create_es_client(hosts=hosts)

    # Resolve directories
    verdicts_dir = args.verdicts_dir
    if verdicts_dir is None:
        # Try common locations
        for candidate in [
            Path("verdicts"),
            Path("/tmp/al-furqan/verdicts"),
            Path.home() / ".al-furqan" / "verdicts",
        ]:
            if candidate.exists():
                verdicts_dir = candidate
                break
        if verdicts_dir is None:
            verdicts_dir = Path("verdicts")
            logger.info("No existing verdicts directory found, using: %s", verdicts_dir)

    feedback_dir = args.feedback_dir or DATA_FEEDBACK

    logger.info("Verdicts directory: %s", verdicts_dir)
    logger.info("Feedback directory: %s", feedback_dir)

    # Migrate
    v_count = migrate_verdicts(es, verdicts_dir, args.prefix, dry_run=args.dry_run)
    f_count = migrate_feedback(es, feedback_dir, args.prefix, dry_run=args.dry_run)

    logger.info("Migration complete: %d verdicts, %d feedback", v_count, f_count)

    if args.verify and not args.dry_run:
        logger.info("Verifying counts...")
        if verify_counts(es, verdicts_dir, feedback_dir, args.prefix):
            logger.info("All counts verified.")
        else:
            logger.error("Count verification FAILED.")


if __name__ == "__main__":
    main()
