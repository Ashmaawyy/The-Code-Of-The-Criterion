"""Phase 1: Create Elasticsearch indices with the arabic_furqan analyzer.

Usage:
    python -m al_furqan.kb.es.setup_indices                  # create all indices
    python -m al_furqan.kb.es.setup_indices --drop            # drop and recreate
    python -m al_furqan.kb.es.setup_indices --index quran     # create one index
    python -m al_furqan.kb.es.setup_indices --test             # verify analyzer works
"""

import argparse
import logging
import sys

from al_furqan import setup_logging
from al_furqan.kb.es.client import create_es_client
from al_furqan.kb.es.indices import INDEX_REGISTRY

logger = logging.getLogger(__name__)

DEFAULT_PREFIX = "furqan"


def create_indices(
    es,
    prefix: str = DEFAULT_PREFIX,
    drop_existing: bool = False,
    only: list[str] | None = None,
) -> dict[str, bool]:
    """Create all (or selected) indices.

    Returns a dict mapping index name → True if created, False if skipped.
    """
    targets = only or list(INDEX_REGISTRY.keys())
    results = {}

    for name in targets:
        if name not in INDEX_REGISTRY:
            logger.error("Unknown index: %s (available: %s)",
                         name, ", ".join(INDEX_REGISTRY.keys()))
            results[name] = False
            continue

        full_name = f"{prefix}_{name}"
        definition = INDEX_REGISTRY[name]

        if es.indices.exists(index=full_name):
            if drop_existing:
                logger.warning("Dropping existing index: %s", full_name)
                es.indices.delete(index=full_name)
            else:
                logger.info("Index already exists, skipping: %s", full_name)
                results[full_name] = False
                continue

        logger.info("Creating index: %s", full_name)
        es.indices.create(index=full_name, body=definition)
        logger.info("Created index: %s", full_name)
        results[full_name] = True

    return results


def test_analyzer(es, prefix: str = DEFAULT_PREFIX) -> bool:
    """Verify the arabic_furqan analyzer works correctly.

    Tests that Arabic text normalization matches the expected output from
    the Python ``normalize_arabic()`` function.
    """
    index = f"{prefix}_quran"
    if not es.indices.exists(index=index):
        logger.error("Index %s does not exist. Run setup first.", index)
        return False

    test_cases = [
        # (input, expected_tokens)
        (
            "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
            ["بسم", "الله", "الرحمان", "الرحيم"],
        ),
        (
            "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ",
            ["انما", "الاعمال", "بالنيات"],
        ),
        (
            "﴿وَكَيْفَ أَخَافُ مَآ أَشْرَكْتُمْ﴾",
            ["وكيف", "اخاف", "ما", "اشركتم"],
        ),
    ]

    all_passed = True
    for text, expected in test_cases:
        response = es.indices.analyze(
            index=index,
            body={"analyzer": "arabic_furqan", "text": text},
        )
        tokens = [t["token"] for t in response["tokens"]]

        if tokens == expected:
            logger.info("PASS: %s → %s", text[:40], tokens)
        else:
            logger.error("FAIL: %s", text[:40])
            logger.error("  Expected: %s", expected)
            logger.error("  Got:      %s", tokens)
            all_passed = False

    return all_passed


def show_status(es, prefix: str = DEFAULT_PREFIX) -> None:
    """Show current index status."""
    for name in INDEX_REGISTRY:
        full_name = f"{prefix}_{name}"
        if es.indices.exists(index=full_name):
            stats = es.indices.stats(index=full_name)
            doc_count = stats["indices"][full_name]["primaries"]["docs"]["count"]
            size = stats["indices"][full_name]["primaries"]["store"]["size_in_bytes"]
            logger.info("  %-20s  %6d docs  %8.1f KB", full_name, doc_count, size / 1024)
        else:
            logger.info("  %-20s  (not created)", full_name)


def main():
    """Entry point."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Create Elasticsearch indices for Al-Furqan")
    parser.add_argument("--drop", action="store_true",
                        help="Drop and recreate existing indices")
    parser.add_argument("--index", nargs="*", default=None,
                        choices=list(INDEX_REGISTRY.keys()),
                        help="Create specific indices (default: all)")
    parser.add_argument("--test", action="store_true",
                        help="Test the arabic_furqan analyzer after creation")
    parser.add_argument("--status", action="store_true",
                        help="Show index status and exit")
    parser.add_argument("--prefix", default=DEFAULT_PREFIX,
                        help=f"Index name prefix (default: {DEFAULT_PREFIX})")
    parser.add_argument("--es-url", default=None,
                        help="Elasticsearch URL (default: from env or localhost:9200)")
    args = parser.parse_args()

    hosts = [args.es_url] if args.es_url else None
    es = create_es_client(hosts=hosts)

    if args.status:
        logger.info("Index status:")
        show_status(es, prefix=args.prefix)
        return

    results = create_indices(
        es, prefix=args.prefix, drop_existing=args.drop, only=args.index,
    )

    created = sum(1 for v in results.values() if v)
    skipped = sum(1 for v in results.values() if not v)
    logger.info("Done: %d created, %d skipped", created, skipped)

    if args.test:
        logger.info("Running analyzer tests...")
        if test_analyzer(es, prefix=args.prefix):
            logger.info("All analyzer tests passed.")
        else:
            logger.error("Some analyzer tests FAILED.")
            sys.exit(1)

    logger.info("Index status after setup:")
    show_status(es, prefix=args.prefix)


if __name__ == "__main__":
    main()
