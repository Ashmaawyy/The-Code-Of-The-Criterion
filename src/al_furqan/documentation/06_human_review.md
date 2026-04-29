# Human Review Interface — Technical Reference

**File:** `human_review.py`
**Role:** The appeals court. Provides a CLI interface for the human reviewer to inspect, approve, correct, or reject verdicts.

## 1. Design Principle

The human reviewer is **not generative** — they do not produce verdicts from scratch. They **calibrate** the system by:

- **Approving** sound verdicts (which become indexed precedent)
- **Correcting** flawed verdicts (field-by-field modification)
- **Rejecting** unsound verdicts (logged but excluded from search)

Over time, the system requires less correction as its precedent base grows.

## 2. Display Functions

### display_verdict(verdict: Verdict)

Pretty-prints a live Verdict object to the terminal with formatted sections:

```
========================================================================
  THE CRITERION — VERDICT
========================================================================

  Question: Is interest-based lending just?
  System:   economic
  Score:    85
  Passes:   1

------------------------------------------------------------------------
  FRICTION POINTS
------------------------------------------------------------------------
  1. Interest contradicts equitable exchange
  2. Debt compounding harms borrowers

------------------------------------------------------------------------
  GATE SCORES
------------------------------------------------------------------------
  [+] Source-Integrity: 85/100 — Survive
      Data is well-documented.
  [+] Structural-Consistency: 70/100 — Survive
      Causal chain traceable.
  [+] Mediation-Zeroing: 90/100 — Survive
      No human preference reliance.

  Origin-Aware Gate: Survive

------------------------------------------------------------------------
  CONSEQUENCES
------------------------------------------------------------------------
  Short-term:
    - Increased debt
  Long-term:
    - Wealth gap

------------------------------------------------------------------------
  REASONING
------------------------------------------------------------------------
  Interest creates systemic debt traps.

------------------------------------------------------------------------
  FINAL JUDGMENT
------------------------------------------------------------------------
  Interest-based lending violates equitable exchange.

========================================================================
```

Gate markers: `[+]` = Survive, `[X]` = Fail.

### display_stored_verdict(data: dict)

Renders a verdict loaded from a JSON file (dict format). Similar layout but also shows ID and status.

## 3. Input Helpers

| Function | Description |
|----------|-------------|
| `prompt_choice(prompt, valid)` | Loops until user enters one of the valid choices. Case-insensitive. |
| `prompt_text(prompt, allow_empty)` | Loops until user enters non-empty text (or any text if `allow_empty=True`). |
| `prompt_int(prompt, min_val, max_val)` | Loops until user enters a valid integer within the range. |
| `prompt_list(prompt)` | Collects items one per line. Empty line finishes the list. |

## 4. Correction Builder

### build_corrected_verdict(original: Verdict) -> Verdict

Walks the reviewer through modifying a verdict field by field. For each field, the reviewer can choose to keep the original value or provide a replacement.

**Fields offered for correction:**

1. **Friction points** — replace the entire list
2. **Gate scores** — for each of the 3 tri-axial gates: new score (0-100), new result (survive/fail), new reasoning
3. **Origin gate** — survive or fail
4. **Short-term consequences** — replace the list
5. **Long-term consequences** — replace the list
6. **Reasoning** — replace the text
7. **Judgment** — replace the text
8. **Total score** — replace the integer

The corrected verdict retains the original question, system type, and pass count. It gets a new timestamp.

## 5. HumanReview Class

### Constructor

```python
HumanReview(store: VerdictStore)
```

### review_verdict(verdict: Verdict) -> str

The primary review workflow. Runs in a loop until a final decision is made.

**Flow:**

```
Display verdict
    │
    ├── [a] Approve
    │   ├── Store as "approved" (indexed)
    │   └── Return verdict_id
    │
    ├── [c] Correct
    │   ├── Walk through field-by-field correction
    │   ├── Display corrected verdict
    │   ├── Confirm?
    │   │   ├── Yes → Store original as "rejected", corrected as "corrected"
    │   │   │         Return corrected verdict_id
    │   │   └── No  → Loop back to display original verdict
    │   │
    │
    └── [r] Reject
        ├── Prompt for rejection reason
        ├── Store as "rejected" (not indexed)
        ├── Append rejection_reason to JSON file
        └── Return verdict_id
```

### browse_verdicts()

Interactive browser for stored verdicts.

1. Shows store statistics (total indexed, total files, by status).
2. Lists the 20 most recent verdict files with status, score, and question preview.
3. User can select a verdict to view details.
4. From details view, user can invalidate (cascade) the verdict.

### search_verdicts()

Semantic search over past verdicts.

1. Prompts for a search query.
2. Retrieves up to 10 results via `VerdictStore.retrieve()`.
3. Displays results with distance, score, and document preview.
4. User can select a result to view the full verdict.

## 6. Review Session (run_review_session)

Standalone interactive menu that provides access to all review functions.

```
Menu:
  [1] Browse stored verdicts
  [2] Search verdicts by topic
  [3] View store statistics
  [4] Review verdicts pending re-review
  [q] Exit review session
```

**Pending re-review (option 4):**
- Scans all JSON files for verdicts with `status == "needs_review"` (flagged by `invalidate_cascade`).
- For each, the reviewer can approve (re-index), reject (remove), or skip.

### Standalone execution

```bash
python human_review.py
```

Creates a default VerdictStore and opens the review session. Useful for reviewing past verdicts without running the full system.
