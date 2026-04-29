"""
Core memory operations: remember, recall, recognize, feedback.

Coordinates SQLite structured storage with ChromaDB vector search
to provide fast pattern matching and semantic recall.
"""

from __future__ import annotations

import time
import uuid

from furqan_memory.storage.sqlite_store import MemoryStore
from furqan_memory.storage.vector_store import MemoryVectorSearch


class MemoryManager:
    """Core memory operations: remember, recall, recognize."""

    def __init__(self, store: MemoryStore, vectors: MemoryVectorSearch):
        self.store = store
        self.vectors = vectors

    def remember(
        self,
        question: str,
        verdict: dict,
        domain: str = "islamic",
        tags: list | None = None,
    ) -> str:
        """Store a verdict in local memory. Returns verdict ID."""
        verdict_id = f"v_{uuid.uuid4().hex[:12]}"
        self.store.save_verdict(verdict_id, question, verdict, domain, tags)
        self.vectors.add_verdict(
            verdict_id,
            question,
            metadata={
                "domain": domain,
                "total_score": verdict.get("total_score", 0),
                "final_judgment": verdict.get("final_judgment", ""),
            },
        )
        return verdict_id

    def recall(
        self,
        query: str,
        domain: str = "all",
        limit: int = 5,
    ) -> list[dict]:
        """Search memory for relevant past verdicts.

        Uses vector similarity to find related verdicts, then enriches
        with full data from SQLite.
        """
        vector_results = self.vectors.search_verdicts(query, limit)

        enriched = []
        for vr in vector_results:
            verdict = self.store.get_verdict(vr["id"])
            if verdict is None:
                continue
            if domain != "all" and verdict.get("domain") != domain:
                continue
            enriched.append({
                "id": vr["id"],
                "score": vr["score"],
                "question": verdict["question"],
                "verdict_data": verdict["verdict_data"],
                "domain": verdict["domain"],
                "tags": verdict.get("tags", []),
                "created_at": verdict["created_at"],
            })
        return enriched

    def recognize(self, query: str, threshold: float = 0.75) -> dict | None:
        """Fast-path: check if query matches a known pattern.

        Target: <50ms response time.
        Returns pattern match dict or None.
        """
        start = time.time()
        matches = self.vectors.search_patterns(query, limit=1)

        if not matches:
            return None

        best = matches[0]
        if best["score"] < threshold:
            return None

        pattern = self.store.get_pattern(best["id"])
        if not pattern or pattern["confidence"] < 0.8:
            return None

        # Update hit tracking
        self.store.update_pattern(
            best["id"],
            {"hit_count": pattern["hit_count"] + 1, "last_hit": time.time()},
        )

        elapsed_ms = (time.time() - start) * 1000
        return {
            "matched": True,
            "pattern": pattern,
            "similarity": best["score"],
            "latency_ms": elapsed_ms,
        }

    def feedback(
        self,
        verdict_id: str,
        rating: str,
        correction: str | None = None,
    ) -> str:
        """Rate a verdict. Adjusts related pattern confidence.

        Args:
            verdict_id: The verdict to rate.
            rating: One of 'positive', 'negative', 'neutral'.
            correction: Optional correction text.

        Returns:
            Feedback ID.
        """
        feedback_id = self.store.save_feedback(
            verdict_id, "verdict", rating, correction
        )

        # Adjust linked pattern confidence if any
        verdict = self.store.get_verdict(verdict_id)
        if verdict:
            # Search for patterns linked to this verdict
            patterns = self.store.get_mature_patterns(min_confidence=0.0)
            for p in patterns:
                if verdict_id in p.get("source_verdicts", []):
                    delta = 0.05 if rating == "positive" else -0.05
                    new_conf = max(0.0, min(1.0, p["confidence"] + delta))
                    self.store.update_pattern(
                        p["id"], {"confidence": new_conf}
                    )

        return feedback_id

    def stats(self, domain: str | None = None) -> dict:
        """Memory usage statistics."""
        base_stats = self.store.get_stats(domain)
        base_stats["vector_verdicts"] = self.vectors.verdicts.count()
        base_stats["vector_patterns"] = self.vectors.patterns.count()
        return base_stats
