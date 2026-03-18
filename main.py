"""
Al-Furqan (The Criterion) — Main Entry Point

Interactive CLI for evaluating questions through the Criterion framework.

Usage:
    python main.py                  # Interactive mode
    python main.py --init           # Generate default config file
    python main.py --review         # Open human review session
    python main.py --stats          # Show verdict store statistics
    python main.py --evaluate "..." # Evaluate a single question
"""

import argparse
import json
import sys
from pathlib import Path

from config import AppConfig, load_config, generate_default_config
from llm_layer import create_llm, LLMProvider
from reasoning_engine import ReasoningEngine, Verdict
from verdict_store import VerdictStore
from human_review import (
    HumanReview,
    display_verdict,
    run_review_session,
    prompt_choice,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BANNER = r"""
 ═══════════════════════════════════════════════════════════════════════════

      ___    __       ______
     /   |  / /      / ____/_  ___________  ____ _____
    / /| | / /______/ /_  / / / / ___/ __ \/ __ `/ __ \
   / ___ |/ /_____/ __/ / /_/ / /  / /_/ / /_/ / / / /
  /_/  |_/_/     /_/    \__,_/_/   \__, /\__,_/_/ /_/
                                     /_/

                     T H E   C R I T E R I O N

 ═══════════════════════════════════════════════════════════════════════════
"""

DIVIDER = "=" * 72
SUB_DIVIDER = "-" * 72


# ---------------------------------------------------------------------------
# System Assembly
# ---------------------------------------------------------------------------

def build_system(config: AppConfig) -> tuple[LLMProvider, ReasoningEngine, VerdictStore, HumanReview]:
    """Assemble all components from config."""
    # LLM layer
    llm = create_llm(config.llm)

    # Reasoning engine
    engine = ReasoningEngine(llm)
    engine.MAX_CORRECTION_PASSES = config.engine.max_correction_passes

    # Verdict store
    store = VerdictStore(
        chroma_dir=Path(config.store.chroma_dir),
        verdicts_dir=Path(config.store.verdicts_dir),
        collection_name=config.store.collection_name,
    )

    # Human review
    review = HumanReview(store)

    return llm, engine, store, review


# ---------------------------------------------------------------------------
# Evaluation Flow
# ---------------------------------------------------------------------------

def run_evaluation(
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
    print(f"\n{SUB_DIVIDER}")
    print(f"  Evaluating: {question}")
    print(SUB_DIVIDER)

    # Retrieve prior verdicts for context
    print("\n  [1/4] Retrieving relevant precedent...")
    context = store.retrieve_as_context(
        question,
        n_results=config.store.default_retrieval_count,
    )
    if context:
        precedent_count = context.count("Prior Verdict")
        print(f"         Found {precedent_count} relevant prior verdict(s).")
    else:
        print("         No prior verdicts found. Reasoning from axioms only.")

    # Run the reasoning pipeline
    print("\n  [2/4] Running The Scan...")
    scan_result = engine.scan(question, context)
    print(f"         System identified: {scan_result.get('primary_system', '?')}")
    print(f"         Friction points: {len(scan_result.get('friction_points', []))}")

    print("\n  [3/4] Running The Mirror (gate evaluation)...")
    mirror_result = engine.mirror(question, scan_result)
    for gate_key in ["gate_1_source_integrity", "gate_2_structural_consistency",
                      "gate_3_mediation_zeroing", "gate_4_origin_aware"]:
        gate = mirror_result.get(gate_key, {})
        name = gate_key.replace("gate_", "").replace("_", " ").title()
        result = gate.get("result", "?")
        score = gate.get("score", "?")
        marker = "[+]" if result == "Survive" else "[X]"
        print(f"         {marker} {name}: {score}/100")

    print("\n  [4/4] Delivering The Verdict...")
    verdict_result = engine.verdict(question, scan_result, mirror_result)

    # Self-correction loop
    print("\n  Running self-correction...")
    passes = 0
    for i in range(1, engine.MAX_CORRECTION_PASSES + 1):
        correction = engine.self_correct(question, verdict_result, i)
        passes = i
        if correction.get("is_sound", False):
            print(f"         Pass {i}: Sound. No contradictions.")
            break
        corrected = correction.get("corrected_verdict")
        if corrected:
            verdict_result = corrected
            contradictions = correction.get("contradictions_found", [])
            print(f"         Pass {i}: {len(contradictions)} contradiction(s) corrected.")
        else:
            print(f"         Pass {i}: Sound.")
            break

    # Build the Verdict object
    verdict = engine._build_verdict_object(question, scan_result, mirror_result, verdict_result, passes)

    # Auto-approve or human review
    threshold = config.review.auto_approve_threshold
    if threshold is not None and verdict.total_score >= threshold:
        print(f"\n  Score {verdict.total_score} >= auto-approve threshold {threshold}.")
        verdict_id = store.store(verdict, status="approved")
        print(f"  Verdict auto-approved. ID: {verdict_id}")
        display_verdict(verdict)
        return verdict_id
    else:
        return review.review_verdict(verdict)


# ---------------------------------------------------------------------------
# Interactive Mode
# ---------------------------------------------------------------------------

def interactive_mode(config: AppConfig) -> None:
    """Main interactive loop."""
    print(BANNER)

    print("  Initializing system...")
    llm, engine, store, review = build_system(config)

    stats = store.stats()
    print(f"  Verdict store: {stats['total_indexed']} indexed, {stats['total_files']} total")
    print(f"  LLM: {config.llm.provider} / {config.llm.model_name}")
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
            print("\n\n  Exiting. Ma'a salama.\n")
            break

        if not user_input:
            continue

        # Commands
        if user_input.lower() == "/quit":
            print("\n  Exiting. Ma'a salama.\n")
            break

        elif user_input.lower() == "/review":
            run_review_session(store)

        elif user_input.lower() == "/stats":
            stats = store.stats()
            print(f"\n  {json.dumps(stats, indent=4)}")

        elif user_input.lower() == "/search":
            review.search_verdicts()

        elif user_input.lower() == "/llm":
            llm_stats = llm.get_stats()
            print(f"\n  {json.dumps(llm_stats, indent=4)}")

        elif user_input.lower() == "/config":
            print(f"\n  {json.dumps(config.to_dict(), indent=4, default=str)}")

        elif user_input.startswith("/"):
            print(f"  Unknown command: {user_input}")
            print("  Available: /review, /stats, /search, /llm, /config, /quit")

        else:
            # Evaluate the question
            try:
                run_evaluation(user_input, engine, store, review, config)
            except ConnectionError as e:
                print(f"\n  Connection error: {e}")
                print("  Make sure your LLM provider is running.")
            except TimeoutError as e:
                print(f"\n  Timeout: {e}")
            except json.JSONDecodeError as e:
                print(f"\n  Failed to parse LLM response as JSON.")
                print(f"  The model may need a more capable variant for structured output.")
                print(f"  Error: {e}")
            except Exception as e:
                print(f"\n  Error during evaluation: {type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
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
        "--evaluate", "-e",
        type=str,
        help="Evaluate a single question (non-interactive)",
    )
    parser.add_argument(
        "--config", "-c",
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
        print(json.dumps(stats, indent=2))
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
        llm, engine, store, review = build_system(config)
        run_evaluation(args.evaluate, engine, store, review, config)
        return

    # Default: interactive mode
    interactive_mode(config)


if __name__ == "__main__":
    main()
