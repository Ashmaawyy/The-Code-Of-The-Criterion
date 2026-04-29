"""Elasticsearch-backed Feedback Store.

Uses the ``furqan_feedback`` index for all storage and retrieval.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field

from elasticsearch import Elasticsearch, NotFoundError


# ---------------------------------------------------------------------------
# HumanFeedback dataclass (canonical location)
# ---------------------------------------------------------------------------

@dataclass
class HumanFeedback:
    """A single piece of human feedback on a verdict."""

    verdict_id: str
    reviewer: str
    rating: str  # "correct", "partially_correct", "incorrect"
    gate_corrections: dict = field(default_factory=dict)
    notes: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "verdict_id": self.verdict_id,
            "reviewer": self.reviewer,
            "rating": self.rating,
            "gate_corrections": self.gate_corrections,
            "notes": self.notes,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HumanFeedback":
        return cls(
            verdict_id=d["verdict_id"],
            reviewer=d["reviewer"],
            rating=d["rating"],
            gate_corrections=d.get("gate_corrections", {}),
            notes=d.get("notes", ""),
            timestamp=d.get("timestamp", 0.0),
        )

logger = logging.getLogger(__name__)

DEFAULT_INDEX = "furqan_feedback"


class ESFeedbackStore:
    """Feedback storage and retrieval backed by Elasticsearch."""

    VALID_RATINGS = {"correct", "partially_correct", "incorrect"}

    def __init__(self, es: Elasticsearch, index: str = DEFAULT_INDEX) -> None:
        self._es = es
        self._index = index

    def _generate_id(self) -> str:
        return f"fb_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    def submit(self, feedback: HumanFeedback) -> str:
        """Submit feedback. Returns feedback ID."""
        if feedback.rating not in self.VALID_RATINGS:
            raise ValueError(
                f"Invalid rating '{feedback.rating}'. Must be one of: {self.VALID_RATINGS}"
            )
        if not feedback.verdict_id:
            raise ValueError("verdict_id is required")
        if not feedback.reviewer:
            raise ValueError("reviewer is required")

        feedback_id = self._generate_id()
        doc = feedback.to_dict()
        doc["feedback_id"] = feedback_id
        doc["timestamp"] = int(feedback.timestamp * 1000)

        self._es.index(index=self._index, id=feedback_id, body=doc, refresh="wait_for")
        return feedback_id

    def get_feedback(self, feedback_id: str) -> HumanFeedback | None:
        """Retrieve feedback by ID."""
        try:
            doc = self._es.get(index=self._index, id=feedback_id)
            return HumanFeedback.from_dict(doc["_source"])
        except NotFoundError:
            return None

    def get_by_verdict(self, verdict_id: str) -> list[HumanFeedback]:
        """Get all feedback for a specific verdict."""
        body = {
            "query": {"term": {"verdict_id": verdict_id}},
            "sort": [{"timestamp": "asc"}],
            "size": 100,
        }
        resp = self._es.search(index=self._index, body=body)
        return [HumanFeedback.from_dict(h["_source"]) for h in resp["hits"]["hits"]]

    def get_stats(self) -> dict:
        """Return feedback statistics."""
        total = self._es.count(index=self._index)["count"]

        body = {
            "size": 0,
            "aggs": {
                "by_rating": {"terms": {"field": "rating", "size": 10}},
                "by_reviewer": {"terms": {"field": "reviewer", "size": 50}},
                "unique_verdicts": {"cardinality": {"field": "verdict_id"}},
            },
        }
        resp = self._es.search(index=self._index, body=body)
        aggs = resp["aggregations"]

        by_rating = {b["key"]: b["doc_count"] for b in aggs["by_rating"]["buckets"]}
        by_reviewer = {b["key"]: b["doc_count"] for b in aggs["by_reviewer"]["buckets"]}

        return {
            "total": total,
            "by_rating": by_rating,
            "by_reviewer": by_reviewer,
            "unique_verdicts_reviewed": aggs["unique_verdicts"]["value"],
        }

    def export(self, export_format: str = "json") -> str:
        """Export all feedback."""
        import json

        body = {"query": {"match_all": {}}, "size": 10000}
        resp = self._es.search(index=self._index, body=body)
        all_feedback = [h["_source"] for h in resp["hits"]["hits"]]

        if export_format == "json":
            return json.dumps(all_feedback, indent=2, ensure_ascii=False)
        if export_format == "jsonl":
            return "\n".join(json.dumps(d, ensure_ascii=False) for d in all_feedback)
        raise ValueError(f"Unsupported format: {export_format}. Use 'json' or 'jsonl'.")
