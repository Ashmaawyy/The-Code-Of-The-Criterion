"""
Al-Furqan (The Criterion) — Main Entry Point

Interactive CLI for evaluating questions through the Criterion framework.

Usage:
    al-furqan                       # Interactive mode
    al-furqan --init                # Generate default config file
    al-furqan --review              # Open human review session
    al-furqan --stats               # Show verdict store statistics
    al-furqan --evaluate "..."      # Evaluate a single question

Or via module:
    python -m al_furqan.cli [options]
"""

import argparse
import json
import logging
from pathlib import Path

from al_furqan import setup_logging
from al_furqan.config import AppConfig, generate_default_config, load_config
from al_furqan.core.reasoning_engine import ReasoningEngine
from al_furqan.kb.es.client import create_es_client
from al_furqan.providers.llm_layer import LLMProvider, create_llm
from al_furqan.review.human_review import (
    HumanReview,
    display_verdict,
    run_review_session,
)
from al_furqan.store.es_verdict_store import ESVerdictStore as VerdictStore

setup_logging()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BANNER = r"""
 ═══════════════════════════════════════════════════════════════════════════

      ___    __       ______
     /   |  / /      / ____/_  ___________  ____ _____
    / /| | / /______/ /_  / / / / ___/ __ \/ __ `/ __ \
   / ___ |/ /_____ / __/ / /_/ / /  / /_/ / /_/ / / / /
  /_/  |_/_/      /_/    \__,_/_/   \__, /\__,_/_/ /_/
                                     /_/

                     T H E   C R I T E R I O N

 ═══════════════════════════════════════════════════════════════════════════
"""

DIVIDER = "=" * 72
SUB_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# System Assembly
# ---------------------------------------------------------------------------


def build_system(
    config: AppConfig,
) -> tuple[LLMProvider, ReasoningEngine, VerdictStore, HumanReview]:
    """Assemble all components from config."""
    # LLM layer
    llm = create_llm(config.llm)

    # Reasoning engine
    engine = ReasoningEngine(llm)
    engine.MAX_CORRECTION_PASSES = config.engine.max_correction_passes  # pylint: disable=invalid-name

    # Verdict store
    es = create_es_client(hosts=config.store.elasticsearch.hosts)
    store = VerdictStore(es=es)

    # Human review
    review = HumanReview(store)

    return llm, engine, store, review


# ---------------------------------------------------------------------------
# Evaluation Flow
# ---------------------------------------------------------------------------


def run_evaluation(  # pylint: disable=too-many-locals
    question: str,
    engine: ReasoningEngine,
    store: VerdictStore,
    review: HumanReview,
    config: AppConfig,
) -> str:
    """
    Run a full evaluation cycle for a single question.

    Returns the verdict ID.
    """
    logger.info(SUB_DIVIDER)
    logger.info("Evaluating: %s", question)
    logger.info(SUB_DIVIDER)

    # Retrieve prior verdicts for context
    logger.info("[1/4] Retrieving relevant precedent...")
    context = store.retrieve_as_context(
        question,
        n_results=config.store.default_retrieval_count,
    )
    if context:
        precedent_count = context.count("Prior Verdict")
        logger.info("Found %d relevant prior verdict(s).", precedent_count)
    else:
        logger.info("No prior verdicts found. Reasoning from axioms only.")

    # Run the reasoning pipeline
    logger.info("[2/4] Running The Scan...")
    scan_result = engine.scan(question, context)
    logger.info("System identified: %s", scan_result.get("primary_system", "?"))
    logger.info("Friction points: %d", len(scan_result.get("friction_points", [])))

    logger.info("[3/4] Running The Mirror (gate evaluation)...")
    mirror_result = engine.mirror(question, scan_result)
    for gate_key in [
        "gate_1_source_integrity",
        "gate_2_structural_consistency",
        "gate_3_mediation_zeroing",
        "gate_4_origin_aware",
    ]:
        gate = mirror_result.get(gate_key, {})
        name = gate_key.replace("gate_", "").replace("_", " ").title()
        result = gate.get("result", "?")
        score = gate.get("score", "?")
        marker = "[+]" if result == "Survive" else "[X]"
        logger.info("%s %s: %s/100", marker, name, score)

    logger.info("[4/4] Delivering The Verdict...")
    verdict_result = engine.verdict(question, scan_result, mirror_result)

    # Self-correction loop
    logger.info("Running self-correction...")
    passes = 0
    for i in range(1, engine.MAX_CORRECTION_PASSES + 1):
        correction = engine.self_correct(question, verdict_result, i)
        passes = i
        if correction.get("is_sound", False):
            logger.info("Pass %d: Sound. No contradictions.", i)
            break
        corrected = correction.get("corrected_verdict")
        if corrected:
            verdict_result = corrected
            contradictions = correction.get("contradictions_found", [])
            logger.info(
                "Pass %d: %d contradiction(s) corrected.", i, len(contradictions)
            )
        else:
            logger.info("Pass %d: Sound.", i)
            break

    # Build the Verdict object
    verdict = engine.build_verdict_object(
        question, scan_result, mirror_result, verdict_result, passes
    )  # pylint: disable=line-too-long

    # Auto-approve or human review
    threshold = config.review.auto_approve_threshold
    if threshold is not None and verdict.total_score >= threshold:  # pylint: disable=no-else-return
        logger.info(
            "Score %s >= auto-approve threshold %s.", verdict.total_score, threshold
        )
        verdict_id = store.store(verdict, status="approved")
        logger.info("Verdict auto-approved. ID: %s", verdict_id)
        display_verdict(verdict)
        return verdict_id
    else:
        return review.review_verdict(verdict)


# ---------------------------------------------------------------------------
# Interactive Mode
# ---------------------------------------------------------------------------


def interactive_mode(config: AppConfig) -> None:  # pylint: disable=too-many-branches, too-many-statements
    """Main interactive loop."""
    print(BANNER)

    logger.info("Initializing system...")
    llm, engine, store, review = build_system(config)

    stats = store.stats()
    logger.info(
        "Verdict store: %d indexed, %d total",
        stats["total_indexed"],
        stats["total_files"],
    )
    logger.info("LLM: %s / %s", config.llm.provider, config.llm.model_name)
    print(f"\n{DIVIDER}")
    print("  Ready. Enter a question to evaluate, or a command:")
    print("    /review  — open human review session")
    print("    /stats   — show verdict store statistics")
    print("    /search  — search past verdicts")
    print("    /llm     — show LLM call statistics")
    print("    /config  — show current configuration")
    print("    /quit    — exit")
    print(DIVIDER)

    while True:
        try:
            print()
            user_input = input("  > ").strip()
        except (KeyboardInterrupt, EOFError):
            logger.info("Exiting. Ma'a salama.")
            break

        if not user_input:
            continue

        # Commands
        if user_input.lower() == "/quit":  # pylint: disable=no-else-break
            logger.info("Exiting. Ma'a salama.")
            break

        elif user_input.lower() == "/review":
            run_review_session(store)

        elif user_input.lower() == "/stats":
            stats = store.stats()
            logger.info("Store statistics:\n%s", json.dumps(stats, indent=4))

        elif user_input.lower() == "/search":
            review.search_verdicts()

        elif user_input.lower() == "/llm":
            llm_stats = llm.get_stats()
            logger.info("LLM statistics:\n%s", json.dumps(llm_stats, indent=4))

        elif user_input.lower() == "/config":
            logger.info(
                "Current configuration:\n%s",
                json.dumps(config.to_dict(), indent=4, default=str),
            )

        elif user_input.startswith("/"):
            logger.warning("Unknown command: %s", user_input)
            logger.info("Available: /review, /stats, /search, /llm, /config, /quit")

        else:
            # Evaluate the question
            try:
                run_evaluation(user_input, engine, store, review, config)
            except ConnectionError as e:
                logger.error("Connection error: %s", e)
                logger.error("Make sure your LLM provider is running.")
            except TimeoutError as e:
                logger.error("Timeout: %s", e)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse LLM response as JSON.")
                logger.error(
                    "The model may need a more capable variant for structured output."
                )
                logger.error("Error: %s", e)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def main():
    """CLI entry point for Al-Furqan (The Criterion)."""
    parser = argparse.ArgumentParser(
        description="Al-Furqan (The Criterion) — Axiom-anchored reasoning engine",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Generate a default config.yaml file",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="Open the human review session",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show verdict store statistics",
    )
    parser.add_argument(
        "--evaluate",
        "-e",
        type=str,
        help="Evaluate a single question (non-interactive)",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Path to config file (default: config.yaml)",
    )

    args = parser.parse_args()

    # --init: generate config and exit
    if args.init:
        generate_default_config()
        return

    # Load config
    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)

    # --stats: show stats and exit
    if args.stats:
        store = VerdictStore(
            chroma_dir=Path(config.store.chroma_dir),
            verdicts_dir=Path(config.store.verdicts_dir),
            collection_name=config.store.collection_name,
        )
        stats = store.stats()
        logger.info("Store statistics:\n%s", json.dumps(stats, indent=2))
        return

    # --review: open review session and exit
    if args.review:
        store = VerdictStore(
            chroma_dir=Path(config.store.chroma_dir),
            verdicts_dir=Path(config.store.verdicts_dir),
            collection_name=config.store.collection_name,
        )
        run_review_session(store)
        return

    # --evaluate: single question evaluation
    if args.evaluate:
        _, engine, store, review = build_system(config)
        try:
            run_evaluation(args.evaluate, engine, store, review, config)
        except ConnectionError as e:
            logger.error("Connection error: %s", e)
        except TimeoutError as e:
            logger.error("Timeout: %s", e)
            logger.error(
                "Try increasing timeout in config.yaml or using a smaller/faster model."
            )
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON: %s", e)
        return

    # Default: interactive mode
    interactive_mode(config)


if __name__ == "__main__":
    main()
