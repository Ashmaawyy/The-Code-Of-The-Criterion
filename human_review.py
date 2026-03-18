"""
Al-Furqan Human Review Interface

The appeals court of the system. Provides a CLI interface for the human
reviewer to inspect, approve, correct, or reject verdicts produced by
the reasoning engine.

The human reviewer is not generative — they do not produce verdicts.
They calibrate the system by confirming good reasoning and correcting
bad reasoning, which the verdict store then learns from.
"""

import json
import time
from typing import Optional

from reasoning_engine import (
    Verdict,
    GateScore,
    GateResult,
)
from verdict_store import VerdictStore


# ---------------------------------------------------------------------------
# Display Helpers
# ---------------------------------------------------------------------------

DIVIDER = "=" * 72
SUB_DIVIDER = "-" * 72


def display_verdict(verdict: Verdict) -> None:
    """Print a formatted verdict to the terminal."""
    print(f"\n{DIVIDER}")
    print("  THE CRITERION — VERDICT")
    print(DIVIDER)

    print(f"\n  Question: {verdict.question}")
    print(f"  System:   {verdict.primary_system.value}")
    print(f"  Score:    {verdict.total_score}")
    print(f"  Passes:   {verdict.passes}")

    print(f"\n{SUB_DIVIDER}")
    print("  FRICTION POINTS")
    print(SUB_DIVIDER)
    if verdict.friction_points:
        for i, fp in enumerate(verdict.friction_points, 1):
            print(f"  {i}. {fp}")
    else:
        print("  None identified.")

    print(f"\n{SUB_DIVIDER}")
    print("  GATE SCORES")
    print(SUB_DIVIDER)
    for g in verdict.gate_scores:
        status_marker = "[+]" if g.result == GateResult.SURVIVE else "[X]"
        print(f"  {status_marker} {g.name}: {g.score}/100 — {g.result.value}")
        print(f"      {g.reasoning}")
    print(f"\n  Origin-Aware Gate: {verdict.origin_gate.value}")

    print(f"\n{SUB_DIVIDER}")
    print("  CONSEQUENCES")
    print(SUB_DIVIDER)
    print("  Short-term:")
    for c in verdict.consequences_short_term:
        print(f"    - {c}")
    print("  Long-term:")
    for c in verdict.consequences_long_term:
        print(f"    - {c}")

    print(f"\n{SUB_DIVIDER}")
    print("  REASONING")
    print(SUB_DIVIDER)
    print(f"  {verdict.revised_reasoning}")

    print(f"\n{SUB_DIVIDER}")
    print("  FINAL JUDGMENT")
    print(SUB_DIVIDER)
    print(f"  {verdict.final_judgment}")
    print(f"\n{DIVIDER}\n")


def display_stored_verdict(data: dict) -> None:
    """Print a stored verdict dict (from JSON file) to the terminal."""
    print(f"\n{DIVIDER}")
    print("  STORED VERDICT")
    print(DIVIDER)

    print(f"\n  ID:       {data.get('id', 'N/A')}")
    print(f"  Status:   {data.get('status', 'N/A')}")
    print(f"  Question: {data.get('question', 'N/A')}")
    print(f"  System:   {data.get('primary_system', 'N/A')}")
    print(f"  Score:    {data.get('total_score', 'N/A')}")

    print(f"\n  Friction Points:")
    for fp in data.get("friction_points", []):
        print(f"    - {fp}")

    print(f"\n  Gate Scores:")
    for g in data.get("gate_scores", []):
        status_marker = "[+]" if g.get("result") == "Survive" else "[X]"
        print(f"    {status_marker} {g.get('name', '?')}: {g.get('score', 0)}/100 — {g.get('result', '?')}")
        print(f"        {g.get('reasoning', '')}")

    print(f"\n  Origin-Aware Gate: {data.get('origin_gate', 'N/A')}")

    print(f"\n  Consequences (short-term):")
    for c in data.get("consequences_short_term", []):
        print(f"    - {c}")
    print(f"  Consequences (long-term):")
    for c in data.get("consequences_long_term", []):
        print(f"    - {c}")

    print(f"\n  Reasoning: {data.get('revised_reasoning', 'N/A')}")
    print(f"\n  Judgment:  {data.get('final_judgment', 'N/A')}")
    print(f"\n{DIVIDER}\n")


# ---------------------------------------------------------------------------
# Input Helpers
# ---------------------------------------------------------------------------

def prompt_choice(prompt: str, valid: list[str]) -> str:
    """Prompt the user until they enter a valid choice."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid:
            return choice
        print(f"  Invalid input. Choose from: {', '.join(valid)}")


def prompt_text(prompt: str, allow_empty: bool = False) -> str:
    """Prompt for text input."""
    while True:
        text = input(prompt).strip()
        if text or allow_empty:
            return text
        print("  Input cannot be empty.")


def prompt_int(prompt: str, min_val: int = 0, max_val: int = 100) -> int:
    """Prompt for an integer within a range."""
    while True:
        raw = input(prompt).strip()
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print(f"  Must be between {min_val} and {max_val}.")
        except ValueError:
            print("  Enter a valid integer.")


def prompt_list(prompt: str) -> list[str]:
    """Prompt for a list of items, one per line. Empty line to finish."""
    print(prompt)
    items = []
    while True:
        item = input("    > ").strip()
        if not item:
            break
        items.append(item)
    return items


# ---------------------------------------------------------------------------
# Correction Builder
# ---------------------------------------------------------------------------

def build_corrected_verdict(original: Verdict) -> Verdict:
    """
    Walk the human reviewer through correcting a verdict field by field.
    Only fields the reviewer chooses to modify are changed.
    """
    print(f"\n{SUB_DIVIDER}")
    print("  CORRECTION MODE")
    print("  Press Enter to keep the original value for each field.")
    print(SUB_DIVIDER)

    # Friction points
    print(f"\n  Current friction points: {original.friction_points}")
    choice = prompt_choice("  Replace friction points? (y/n): ", ["y", "n"])
    if choice == "y":
        friction_points = prompt_list("  Enter corrected friction points (empty line to finish):")
    else:
        friction_points = original.friction_points

    # Gate scores
    print(f"\n  Current gate scores:")
    for g in original.gate_scores:
        print(f"    {g.name}: {g.score}/100 [{g.result.value}]")

    choice = prompt_choice("  Correct gate scores? (y/n): ", ["y", "n"])
    if choice == "y":
        gate_scores = []
        for g in original.gate_scores:
            print(f"\n    Correcting: {g.name}")
            new_score = prompt_int(f"      Score (0-100) [{g.score}]: ", 0, 100)
            result_str = prompt_choice(
                f"      Result (survive/fail) [{g.result.value.lower()}]: ",
                ["survive", "fail"],
            )
            new_result = GateResult.SURVIVE if result_str == "survive" else GateResult.FAIL
            reasoning = prompt_text(f"      Reasoning [{g.reasoning[:50]}...]: ", allow_empty=True)
            gate_scores.append(GateScore(
                name=g.name,
                score=new_score,
                result=new_result,
                reasoning=reasoning if reasoning else g.reasoning,
            ))
    else:
        gate_scores = original.gate_scores

    # Origin gate
    print(f"\n  Current origin gate: {original.origin_gate.value}")
    choice = prompt_choice("  Correct origin gate? (y/n): ", ["y", "n"])
    if choice == "y":
        origin_str = prompt_choice("    Result (survive/fail): ", ["survive", "fail"])
        origin_gate = GateResult.SURVIVE if origin_str == "survive" else GateResult.FAIL
    else:
        origin_gate = original.origin_gate

    # Consequences
    print(f"\n  Current short-term consequences: {original.consequences_short_term}")
    choice = prompt_choice("  Replace short-term consequences? (y/n): ", ["y", "n"])
    if choice == "y":
        consequences_short = prompt_list("  Enter corrected short-term consequences:")
    else:
        consequences_short = original.consequences_short_term

    print(f"\n  Current long-term consequences: {original.consequences_long_term}")
    choice = prompt_choice("  Replace long-term consequences? (y/n): ", ["y", "n"])
    if choice == "y":
        consequences_long = prompt_list("  Enter corrected long-term consequences:")
    else:
        consequences_long = original.consequences_long_term

    # Reasoning
    print(f"\n  Current reasoning: {original.revised_reasoning[:100]}...")
    choice = prompt_choice("  Replace reasoning? (y/n): ", ["y", "n"])
    if choice == "y":
        revised_reasoning = prompt_text("  Enter corrected reasoning:\n    > ")
    else:
        revised_reasoning = original.revised_reasoning

    # Judgment
    print(f"\n  Current judgment: {original.final_judgment[:100]}...")
    choice = prompt_choice("  Replace judgment? (y/n): ", ["y", "n"])
    if choice == "y":
        final_judgment = prompt_text("  Enter corrected judgment:\n    > ")
    else:
        final_judgment = original.final_judgment

    # Score
    print(f"\n  Current total score: {original.total_score}")
    choice = prompt_choice("  Correct score? (y/n): ", ["y", "n"])
    if choice == "y":
        total_score = prompt_int("  Enter corrected score: ", 0, 1000)
    else:
        total_score = original.total_score

    return Verdict(
        question=original.question,
        primary_system=original.primary_system,
        friction_points=friction_points,
        gate_scores=gate_scores,
        origin_gate=origin_gate,
        consequences_short_term=consequences_short,
        consequences_long_term=consequences_long,
        revised_reasoning=revised_reasoning,
        final_judgment=final_judgment,
        total_score=total_score,
        passes=original.passes,
        timestamp=time.time(),
    )


# ---------------------------------------------------------------------------
# Human Review Session
# ---------------------------------------------------------------------------

class HumanReview:
    """
    CLI interface for the human appeals court.

    Provides workflows for:
    - Reviewing a freshly generated verdict (approve/correct/reject)
    - Browsing and re-reviewing stored verdicts
    - Viewing verdict store statistics
    - Invalidating verdicts with cascade detection
    """

    def __init__(self, store: VerdictStore):
        self.store = store

    def review_verdict(self, verdict: Verdict) -> str:
        """
        Review a single verdict. Returns the verdict ID after storage.

        Flow:
        1. Display the verdict
        2. Human chooses: approve, correct, or reject
        3. If correct: walk through field-by-field correction
        4. Store with appropriate status
        """
        while True:
            display_verdict(verdict)

            print("  What is your ruling?")
            print("    [a] Approve — verdict is sound, index for future precedent")
            print("    [c] Correct — verdict has errors, provide corrections")
            print("    [r] Reject  — verdict is unsound, log but do not index")
            print()

            choice = prompt_choice("  Ruling (a/c/r): ", ["a", "c", "r"])

            if choice == "a":
                verdict_id = self.store.store(verdict, status="approved")
                print(f"\n  Verdict APPROVED and indexed. ID: {verdict_id}")
                return verdict_id

            elif choice == "c":
                corrected = build_corrected_verdict(verdict)
                print("\n  Corrected verdict:")
                display_verdict(corrected)

                confirm = prompt_choice("  Confirm correction? (y/n): ", ["y", "n"])
                if confirm == "y":
                    # Store original as rejected, corrected as new
                    self.store.store(verdict, status="rejected")
                    verdict_id = self.store.store(corrected, status="corrected")
                    print(f"\n  Original rejected. Corrected verdict indexed. ID: {verdict_id}")
                    return verdict_id
                else:
                    print("  Correction discarded. Returning to review.")
                    continue  # loop back to review the same verdict

            else:  # reject
                reason = prompt_text("  Reason for rejection: ")
                verdict_id = self.store.store(verdict, status="rejected")
                # Append rejection reason to the log file
                log_path = self.store.verdicts_dir / f"{verdict_id}.json"
                with open(log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["rejection_reason"] = reason
                with open(log_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"\n  Verdict REJECTED and logged. ID: {verdict_id}")
                return verdict_id

    def browse_verdicts(self) -> None:
        """Browse stored verdicts and optionally re-review them."""
        stats = self.store.stats()
        print(f"\n{DIVIDER}")
        print("  VERDICT STORE")
        print(DIVIDER)
        print(f"  Total indexed: {stats['total_indexed']}")
        print(f"  Total files:   {stats['total_files']}")
        print(f"  By status:")
        for status, count in stats.get("by_status", {}).items():
            print(f"    {status}: {count}")
        print()

        # List verdict files
        verdict_files = sorted(self.store.verdicts_dir.glob("*.json"), reverse=True)
        if not verdict_files:
            print("  No verdicts stored yet.")
            return

        print("  Recent verdicts:")
        display_list = verdict_files[:20]  # show last 20
        for i, path in enumerate(display_list, 1):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            question_preview = data.get("question", "")[:60]
            status = data.get("status", "?")
            score = data.get("total_score", "?")
            print(f"  {i:3}. [{status:>10}] (score: {score}) {question_preview}...")

        print(f"\n  Enter a number to view details, or 'q' to go back.")
        while True:
            choice = input("  > ").strip()
            if choice.lower() == "q":
                break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(display_list):
                    with open(display_list[idx], "r", encoding="utf-8") as f:
                        data = json.load(f)
                    display_stored_verdict(data)

                    # Offer actions
                    print("  Actions:")
                    print("    [i] Invalidate (cascade)")
                    print("    [q] Back to list")
                    action = prompt_choice("  Action (i/q): ", ["i", "q"])

                    if action == "i":
                        verdict_id = data.get("id", "")
                        if verdict_id:
                            flagged = self.store.invalidate_cascade(verdict_id)
                            print(f"\n  Verdict {verdict_id} invalidated.")
                            if flagged:
                                print(f"  Flagged {len(flagged)} downstream verdicts for re-review:")
                                for fid in flagged:
                                    print(f"    - {fid}")
                            else:
                                print("  No downstream verdicts affected.")
                else:
                    print("  Invalid number.")
            except ValueError:
                print("  Enter a number or 'q'.")

    def search_verdicts(self) -> None:
        """Search past verdicts by semantic similarity."""
        query = prompt_text("\n  Search query: ")
        results = self.store.retrieve(query, n_results=10)

        if not results:
            print("  No matching verdicts found.")
            return

        print(f"\n  Found {len(results)} relevant verdicts:\n")
        for i, r in enumerate(results, 1):
            distance = r.get("distance")
            dist_str = f"{distance:.4f}" if distance is not None else "N/A"
            meta = r.get("metadata", {})
            doc_preview = r.get("document", "")[:80]
            print(f"  {i}. [dist: {dist_str}] (score: {meta.get('total_score', '?')}) {doc_preview}...")

        print(f"\n  Enter a number to view full verdict, or 'q' to go back.")
        while True:
            choice = input("  > ").strip()
            if choice.lower() == "q":
                break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(results):
                    verdict_id = results[idx]["id"]
                    data = self.store.get_verdict_by_id(verdict_id)
                    if data:
                        display_stored_verdict(data)
                    else:
                        print(f"  Could not load verdict file for {verdict_id}.")
                else:
                    print("  Invalid number.")
            except ValueError:
                print("  Enter a number or 'q'.")


# ---------------------------------------------------------------------------
# Interactive Menu
# ---------------------------------------------------------------------------

def run_review_session(store: VerdictStore) -> None:
    """
    Run an interactive human review session.

    This is meant to be called from main.py after verdicts are generated,
    or standalone to review/browse past verdicts.
    """
    review = HumanReview(store)

    print(f"\n{DIVIDER}")
    print("  AL-FURQAN — HUMAN REVIEW INTERFACE")
    print("  The Appeals Court")
    print(DIVIDER)

    while True:
        print("\n  Menu:")
        print("    [1] Browse stored verdicts")
        print("    [2] Search verdicts by topic")
        print("    [3] View store statistics")
        print("    [4] Review verdicts pending re-review")
        print("    [q] Exit review session")
        print()

        choice = input("  > ").strip().lower()

        if choice == "1":
            review.browse_verdicts()

        elif choice == "2":
            review.search_verdicts()

        elif choice == "3":
            stats = store.stats()
            print(f"\n  {json.dumps(stats, indent=4)}")

        elif choice == "4":
            # Find verdicts with needs_review status
            pending = []
            for path in store.verdicts_dir.glob("*.json"):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("status") == "needs_review":
                    pending.append(data)

            if not pending:
                print("\n  No verdicts pending re-review.")
                continue

            print(f"\n  {len(pending)} verdict(s) pending re-review:\n")
            for i, data in enumerate(pending, 1):
                question_preview = data.get("question", "")[:60]
                print(f"  {i}. {question_preview}...")

            print(f"\n  Enter a number to review, or 'q' to go back.")
            while True:
                pick = input("  > ").strip()
                if pick.lower() == "q":
                    break
                try:
                    idx = int(pick) - 1
                    if 0 <= idx < len(pending):
                        display_stored_verdict(pending[idx])
                        print("  Actions:")
                        print("    [a] Approve (re-index)")
                        print("    [r] Reject (remove from index)")
                        print("    [s] Skip")
                        action = prompt_choice("  Action (a/r/s): ", ["a", "r", "s"])
                        verdict_id = pending[idx].get("id", "")
                        if action == "a":
                            store.update_status(verdict_id, "approved")
                            print(f"  Verdict {verdict_id} re-approved.")
                        elif action == "r":
                            store.update_status(verdict_id, "rejected")
                            print(f"  Verdict {verdict_id} rejected.")
                        # skip does nothing
                    else:
                        print("  Invalid number.")
                except ValueError:
                    print("  Enter a number or 'q'.")

        elif choice == "q":
            print("\n  Exiting review session.\n")
            break

        else:
            print("  Invalid choice.")


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    store = VerdictStore()
    run_review_session(store)
