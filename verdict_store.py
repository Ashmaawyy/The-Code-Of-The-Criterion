"""
Al-Furqan Verdict Store

Vector database layer for storing and retrieving verdicts.
Uses ChromaDB for local vector storage with semantic search over
past verdicts and their reasoning patterns.

This is the "memory" of the system — enabling case-law style
precedent retrieval for the reasoning engine.
"""

import json
import time
from pathlib import Path
from typing import Optional

import chromadb

from reasoning_engine import Verdict, GateResult, SystemType, GateScore


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERDICTS_DIR = Path(__file__).parent / "verdicts"
CHROMA_DIR = Path(__file__).parent / ".chroma_db"
COLLECTION_NAME = "criterion_verdicts"
DEFAULT_N_RESULTS = 5


# ---------------------------------------------------------------------------
# Verdict Store
# ---------------------------------------------------------------------------

class VerdictStore:
    """
    Persistent verdict storage with semantic retrieval.

    Stores each verdict as:
    - A document in ChromaDB (for semantic search)
    - A JSON file in verdicts/ (for human-readable logs and backup)

    Retrieves relevant past verdicts by semantic similarity to a new question,
    enabling the reasoning engine to build on precedent.
    """

    def __init__(
        self,
        chroma_dir: Optional[Path] = None,
        verdicts_dir: Optional[Path] = None,
        collection_name: Optional[str] = None,
    ):
        self.verdicts_dir = verdicts_dir or VERDICTS_DIR
        self.verdicts_dir.mkdir(parents=True, exist_ok=True)

        chroma_path = chroma_dir or CHROMA_DIR
        chroma_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(chroma_path))
        self.collection = self.client.get_or_create_collection(
            name=collection_name or COLLECTION_NAME,
            metadata={"description": "Al-Furqan Criterion verdicts and reasoning patterns"},
        )

    def _verdict_to_document(self, verdict: Verdict) -> str:
        """
        Convert a verdict into a single text document for embedding.

        Combines the question, reasoning, friction points, and judgment
        into a unified string that captures the full reasoning pattern.
        """
        parts = [
            f"Question: {verdict.question}",
            f"System: {verdict.primary_system.value}",
            f"Friction Points: {'; '.join(verdict.friction_points)}",
            f"Reasoning: {verdict.revised_reasoning}",
            f"Judgment: {verdict.final_judgment}",
        ]
        return "\n".join(parts)

    def _verdict_to_metadata(self, verdict: Verdict) -> dict:
        """Extract searchable metadata from a verdict."""
        return {
            "primary_system": verdict.primary_system.value,
            "origin_gate": verdict.origin_gate.value,
            "total_score": verdict.total_score,
            "passes": verdict.passes,
            "timestamp": verdict.timestamp,
            "gate_1_score": verdict.gate_scores[0].score if len(verdict.gate_scores) > 0 else 0,
            "gate_2_score": verdict.gate_scores[1].score if len(verdict.gate_scores) > 1 else 0,
            "gate_3_score": verdict.gate_scores[2].score if len(verdict.gate_scores) > 2 else 0,
        }

    def _generate_id(self, verdict: Verdict) -> str:
        """Generate a unique ID for a verdict based on timestamp."""
        ts = str(verdict.timestamp).replace(".", "_")
        return f"verdict_{ts}"

    def store(self, verdict: Verdict, status: str = "approved") -> str:
        """
        Store a verdict in both ChromaDB and as a JSON file.

        Args:
            verdict: The Verdict object to store.
            status: One of 'approved', 'corrected', 'rejected'.
                    Only 'approved' and 'corrected' are indexed for retrieval.

        Returns:
            The verdict ID.
        """
        verdict_id = self._generate_id(verdict)

        # Save JSON log file
        log_data = verdict.to_dict()
        log_data["id"] = verdict_id
        log_data["status"] = status
        log_path = self.verdicts_dir / f"{verdict_id}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        # Index in ChromaDB only if approved or corrected
        if status in ("approved", "corrected"):
            document = self._verdict_to_document(verdict)
            metadata = self._verdict_to_metadata(verdict)
            metadata["status"] = status

            self.collection.upsert(
                ids=[verdict_id],
                documents=[document],
                metadatas=[metadata],
            )

        return verdict_id

    def retrieve(self, question: str, n_results: int = DEFAULT_N_RESULTS,
                 system_filter: Optional[SystemType] = None) -> list[dict]:
        """
        Retrieve the most relevant past verdicts for a given question.

        Args:
            question: The new question to find precedent for.
            n_results: Max number of results to return.
            system_filter: Optional filter by system type.

        Returns:
            List of dicts with 'document', 'metadata', 'distance' keys,
            sorted by relevance (closest first).
        """
        where_filter = None
        if system_filter:
            where_filter = {"primary_system": system_filter.value}

        # Guard against querying empty collection
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[question],
            n_results=min(n_results, self.collection.count()),
            where=where_filter,
        )

        verdicts = []
        for i in range(len(results["ids"][0])):
            verdicts.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })

        return verdicts

    def retrieve_as_context(self, question: str, n_results: int = DEFAULT_N_RESULTS) -> str:
        """
        Retrieve past verdicts and format them as context string
        for the reasoning engine.

        This is the primary interface between the verdict store
        and the reasoning engine's evaluate() method.
        """
        results = self.retrieve(question, n_results)
        if not results:
            return ""

        context_parts = []
        for i, r in enumerate(results, 1):
            dist = r['distance']
            dist_str = f"{dist:.4f}" if dist is not None else "N/A"
            context_parts.append(f"--- Prior Verdict {i} (relevance distance: {dist_str}) ---")
            context_parts.append(r["document"])
            context_parts.append(f"Score: {r['metadata'].get('total_score', 'N/A')}")
            context_parts.append(f"Status: {r['metadata'].get('status', 'N/A')}")
            context_parts.append("")

        return "\n".join(context_parts)

    def get_verdict_by_id(self, verdict_id: str) -> Optional[dict]:
        """Load a full verdict from its JSON file."""
        log_path = self.verdicts_dir / f"{verdict_id}.json"
        if not log_path.exists():
            return None
        with open(log_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def update_status(self, verdict_id: str, new_status: str,
                      corrected_verdict: Optional[Verdict] = None) -> bool:
        """
        Update a verdict's status (used by human review).

        If status changes to 'rejected', removes from ChromaDB index.
        If a corrected verdict is provided, replaces the old one.

        Args:
            verdict_id: The ID of the verdict to update.
            new_status: New status ('approved', 'corrected', 'rejected').
            corrected_verdict: Optional replacement verdict (for corrections).

        Returns:
            True if update succeeded.
        """
        log_path = self.verdicts_dir / f"{verdict_id}.json"
        if not log_path.exists():
            return False

        if corrected_verdict:
            # Store the corrected version as a new entry
            self.store(corrected_verdict, status="corrected")
            # Mark original as superseded
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["status"] = "superseded"
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            # Remove old from index
            try:
                self.collection.delete(ids=[verdict_id])
            except Exception:
                pass
        elif new_status == "rejected":
            # Update file
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["status"] = "rejected"
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            # Remove from index
            try:
                self.collection.delete(ids=[verdict_id])
            except Exception:
                pass
        else:
            # Update file status
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["status"] = new_status
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            if new_status in ("approved", "corrected"):
                # Re-index: reconstruct document and metadata from stored data
                verdict_obj = Verdict.from_dict(data)
                document = self._verdict_to_document(verdict_obj)
                metadata = self._verdict_to_metadata(verdict_obj)
                metadata["status"] = new_status
                self.collection.upsert(
                    ids=[verdict_id],
                    documents=[document],
                    metadatas=[metadata],
                )
            elif new_status not in ("approved", "corrected"):
                # Remove from index for any non-indexed status (needs_review, etc.)
                try:
                    self.collection.delete(ids=[verdict_id])
                except Exception:
                    pass

        return True

    def invalidate_cascade(self, verdict_id: str) -> list[str]:
        """
        Retroactively invalidate a verdict and flag any verdicts
        that may have used it as precedent.

        Returns list of verdict IDs that were flagged for re-review.

        NOTE: Full cascade detection requires storing which prior verdicts
        were retrieved during each evaluation. This is a simplified version
        that flags verdicts created after the invalidated one with
        similar content.
        """
        original = self.get_verdict_by_id(verdict_id)
        if not original:
            return []

        # Mark as invalidated
        self.update_status(verdict_id, "rejected")

        # Find potentially affected verdicts (created after, similar content)
        original_time = original.get("timestamp", 0)
        question = original.get("question", "")

        if not question:
            return []

        similar = self.retrieve(question, n_results=20)
        flagged = []
        for s in similar:
            s_time = s["metadata"].get("timestamp", 0)
            if s_time > original_time and s["id"] != verdict_id:
                # Flag for re-review
                self.update_status(s["id"], "needs_review")
                flagged.append(s["id"])

        return flagged

    def stats(self) -> dict:
        """Return summary statistics about the verdict store."""
        total_indexed = self.collection.count()
        total_files = len(list(self.verdicts_dir.glob("*.json")))

        # Count by status from files
        status_counts = {}
        for path in self.verdicts_dir.glob("*.json"):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            status = data.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_indexed": total_indexed,
            "total_files": total_files,
            "by_status": status_counts,
        }
