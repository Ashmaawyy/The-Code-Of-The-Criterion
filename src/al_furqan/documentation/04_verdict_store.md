# Verdict Store — Technical Reference

**File:** `verdict_store.py`
**Role:** The persistent memory of the system. Stores verdicts, retrieves relevant precedent via semantic search, and maintains index consistency across status changes.

## 1. Overview

The verdict store implements a dual-storage strategy:

1. **ChromaDB** — a local vector database for semantic similarity search. Used to retrieve relevant past verdicts when evaluating new questions (RAG pattern).
2. **JSON files** — one file per verdict in the `verdicts/` directory. Human-readable, serves as the audit trail and backup.

Only `approved` and `corrected` verdicts are indexed in ChromaDB. Rejected, superseded, and needs_review verdicts are stored as JSON files but excluded from search, so they cannot pollute future reasoning.

## 2. Constants

| Constant | Default | Description |
|----------|---------|-------------|
| `VERDICTS_DIR` | `<project>/verdicts/` | Directory for JSON log files |
| `CHROMA_DIR` | `<project>/.chroma_db/` | Directory for ChromaDB persistent storage |
| `COLLECTION_NAME` | `"criterion_verdicts"` | ChromaDB collection name |
| `DEFAULT_N_RESULTS` | `5` | Default number of results for retrieval |

All of these can be overridden via constructor parameters or config.

## 3. VerdictStore Class

### Constructor

```python
VerdictStore(
    chroma_dir: Optional[Path] = None,
    verdicts_dir: Optional[Path] = None,
    collection_name: Optional[str] = None,
)
```

Creates directories if they don't exist. Initializes a `chromadb.PersistentClient` and gets or creates the named collection.

### Public Methods

#### store(verdict, status) -> str

Stores a verdict in both ChromaDB and as a JSON file.

**Parameters:**
- `verdict: Verdict` — The verdict object to store.
- `status: str` — One of `"approved"`, `"corrected"`, `"rejected"`. Only `approved` and `corrected` are indexed in ChromaDB.

**Returns:** The verdict ID (format: `verdict_{timestamp}`).

**Behavior:**
1. Generates a unique ID from the verdict's timestamp.
2. Serializes the verdict to dict, adds `id` and `status` fields.
3. Writes the JSON file to `verdicts/{verdict_id}.json`.
4. If status is `approved` or `corrected`: converts to embedding document and metadata, upserts into ChromaDB.

#### retrieve(question, n_results, system_filter) -> list[dict]

Retrieves the most relevant past verdicts for a given question via semantic similarity search.

**Parameters:**
- `question: str` — The new question to find precedent for.
- `n_results: int` — Maximum number of results (default 5).
- `system_filter: Optional[SystemType]` — Optional filter by system type.

**Returns:** List of dicts, each containing:
- `id` — Verdict ID
- `document` — The embedded text document
- `metadata` — All stored metadata (system type, scores, status, timestamp)
- `distance` — Semantic distance (lower = more relevant). May be `None`.

Returns empty list if the collection is empty.

#### retrieve_as_context(question, n_results) -> str

Retrieves past verdicts and formats them as a single context string suitable for injection into the reasoning engine's prompts.

**Format of each entry:**
```
--- Prior Verdict 1 (relevance distance: 0.1234) ---
Question: ...
System: ...
Friction Points: ...
Reasoning: ...
Judgment: ...
Score: 85
Status: approved
```

Returns empty string if no prior verdicts exist.

#### get_verdict_by_id(verdict_id) -> Optional[dict]

Loads a full verdict from its JSON file. Returns `None` if the file doesn't exist.

#### update_status(verdict_id, new_status, corrected_verdict) -> bool

Updates a verdict's status and synchronizes the ChromaDB index.

**Parameters:**
- `verdict_id: str` — ID of the verdict to update.
- `new_status: str` — New status value.
- `corrected_verdict: Optional[Verdict]` — If provided, stores this as a new corrected entry and marks the original as superseded.

**Index synchronization behavior:**

| Scenario | JSON File | ChromaDB |
|----------|-----------|----------|
| `corrected_verdict` provided | Original → `superseded` | Original deleted; corrected upserted |
| `new_status == "rejected"` | Updated to `rejected` | Deleted from index |
| `new_status == "approved"` | Updated to `approved` | Re-upserted (re-indexed) |
| `new_status == "needs_review"` | Updated to `needs_review` | Deleted from index |
| Any other non-indexed status | Updated | Deleted from index |

**Returns:** `True` if the file existed and was updated, `False` if the verdict ID was not found.

#### invalidate_cascade(verdict_id) -> list[str]

Retroactively invalidates a verdict and flags potentially affected downstream verdicts for re-review.

**Algorithm:**
1. Load the original verdict.
2. Mark it as `rejected` (removes from index).
3. Search for semantically similar verdicts that were created *after* the original.
4. Mark those as `needs_review` (removes from index).
5. Return the list of flagged verdict IDs.

**Limitation:** This is a simplified cascade detection based on semantic similarity and timestamp ordering. Full cascade tracking would require storing which prior verdicts were retrieved as context during each evaluation.

#### stats() -> dict

Returns summary statistics.

```json
{
    "total_indexed": 42,
    "total_files": 50,
    "by_status": {
        "approved": 35,
        "corrected": 7,
        "rejected": 5,
        "needs_review": 3
    }
}
```

### Internal Methods

| Method | Description |
|--------|-------------|
| `_verdict_to_document(verdict)` | Converts a Verdict into a single text string for embedding. Combines question, system type, friction points, reasoning, and judgment. |
| `_verdict_to_metadata(verdict)` | Extracts searchable metadata: system type, gate scores (individual), total score, passes, timestamp, origin gate result. |
| `_generate_id(verdict)` | Generates a unique ID from the verdict's timestamp: `verdict_{timestamp_with_underscores}`. |

## 4. Embedding Strategy

The document stored in ChromaDB for each verdict combines five fields:

```
Question: {question}
System: {system_type}
Friction Points: {friction_points joined by "; "}
Reasoning: {revised_reasoning}
Judgment: {final_judgment}
```

This captures the full reasoning pattern — not just the question surface form — so that semantic search finds verdicts with similar *reasoning*, not just similar *wording*.

ChromaDB uses its default embedding model (all-MiniLM-L6-v2) to embed these documents. The semantic distance returned in retrieval results indicates how conceptually similar two verdicts' reasoning patterns are.

## 5. Verdict Statuses

| Status | Meaning | In ChromaDB Index? |
|--------|---------|-------------------|
| `approved` | Human confirmed as sound | Yes |
| `corrected` | Human corrected and confirmed | Yes |
| `rejected` | Human rejected as unsound | No |
| `superseded` | Replaced by a corrected version | No |
| `needs_review` | Flagged by cascade invalidation | No |
