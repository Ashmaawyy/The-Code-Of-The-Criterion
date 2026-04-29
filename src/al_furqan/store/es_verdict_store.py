"""Elasticsearch-backed Verdict Store.

Drop-in replacement for ``store/verdict_store.py``.  Uses the
``furqan_verdicts`` index for both storage and semantic retrieval,
replacing both the JSON file store and ChromaDB vector store.
"""

import logging
import uuid
from typing import Optional

from elasticsearch import Elasticsearch, NotFoundError

from al_furqan.core.reasoning_engine import Verdict, SystemType

logger = logging.getLogger(__name__)

DEFAULT_INDEX = "furqan_verdicts"
DEFAULT_N_RESULTS = 5


class ESVerdictStore:
    """Verdict storage and retrieval backed by Elasticsearch.

    Stores verdicts as ES documents with dense_vector embedding for
    semantic similarity search — replaces both JSON files and ChromaDB.
    """

    def __init__(
        self,
        es: Elasticsearch,
        index: str = DEFAULT_INDEX,
        embed_fn=None,
    ) -> None:
        """
        Args:
            es: Elasticsearch client.
            index: Index name for verdicts.
            embed_fn: callable(str) -> list[float] for generating embeddings.
                      If None, semantic search is disabled.
        """
        self._es = es
        self._index = index
        self._embed_fn = embed_fn

    def _verdict_to_document_text(self, verdict: Verdict) -> str:
        """Build the text used for embedding — matches legacy VerdictStore."""
        return (
            f"Question: {verdict.question}\n"
            f"System: {verdict.primary_system.value}\n"
            f"Friction Points: {'; '.join(verdict.friction_points)}\n"
            f"Reasoning: {verdict.revised_reasoning}\n"
            f"Judgment: {verdict.final_judgment}"
        )

    def _generate_id(self, verdict: Verdict) -> str:
        ts = int(verdict.timestamp)
        return f"verdict_{ts}_{uuid.uuid4().hex[:8]}"

    def store(self, verdict: Verdict, status: str = "approved") -> str:
        """Store a verdict. Returns the verdict ID."""
        verdict_id = self._generate_id(verdict)

        gate_scores = [
            {"gate_id": gs.name, "score": gs.score, "reasoning": gs.reasoning}
            for gs in verdict.gate_scores
        ]

        doc = {
            "verdict_id": verdict_id,
            "question": verdict.question,
            "primary_system": verdict.primary_system.value,
            "origin_gate": verdict.origin_gate.value,
            "friction_points": verdict.friction_points,
            "revised_reasoning": verdict.revised_reasoning,
            "final_judgment": verdict.final_judgment,
            "total_score": verdict.total_score,
            "passes": verdict.passes,
            "status": status,
            "timestamp": int(verdict.timestamp * 1000),
            "gate_scores": gate_scores,
        }

        # Generate embedding if available
        if self._embed_fn and status in ("approved", "corrected"):
            text = self._verdict_to_document_text(verdict)
            doc["embedding"] = self._embed_fn(text)

        self._es.index(index=self._index, id=verdict_id, body=doc, refresh="wait_for")
        logger.info("Verdict stored: %s (status=%s)", verdict_id, status)
        return verdict_id

    def retrieve(
        self,
        question: str,
        n_results: int = DEFAULT_N_RESULTS,
        system_filter: Optional[SystemType] = None,
    ) -> list[dict]:
        """Retrieve relevant past verdicts for a question.

        Uses knn vector search if embeddings are available, falls back to
        text search otherwise.
        """
        if self._embed_fn:
            return self._retrieve_semantic(question, n_results, system_filter)
        return self._retrieve_text(question, n_results, system_filter)

    def _retrieve_semantic(self, question: str, n_results: int,
                           system_filter: Optional[SystemType]) -> list[dict]:
        """Retrieve using knn vector similarity."""
        embedding = self._embed_fn(question)

        knn_filter = [{"terms": {"status": ["approved", "corrected"]}}]
        if system_filter:
            knn_filter.append({"term": {"primary_system": system_filter.value}})

        body = {
            "knn": {
                "field": "embedding",
                "query_vector": embedding,
                "k": n_results,
                "num_candidates": n_results * 10,
                "filter": {"bool": {"must": knn_filter}},
            },
        }
        resp = self._es.search(index=self._index, body=body)
        return self._hits_to_results(resp)

    def _retrieve_text(self, question: str, n_results: int,
                       system_filter: Optional[SystemType]) -> list[dict]:
        """Fallback: retrieve using text similarity."""
        must = [{"match": {"question": question}}]
        filters = [{"terms": {"status": ["approved", "corrected"]}}]
        if system_filter:
            filters.append({"term": {"primary_system": system_filter.value}})

        body = {
            "query": {"bool": {"must": must, "filter": filters}},
            "size": n_results,
        }
        resp = self._es.search(index=self._index, body=body)
        return self._hits_to_results(resp)

    def _hits_to_results(self, resp: dict) -> list[dict]:
        results = []
        for hit in resp["hits"]["hits"]:
            src = hit["_source"]
            results.append({
                "id": hit["_id"],
                "document": (
                    f"Question: {src.get('question', '')}\n"
                    f"System: {src.get('primary_system', '')}\n"
                    f"Reasoning: {src.get('revised_reasoning', '')}\n"
                    f"Judgment: {src.get('final_judgment', '')}"
                ),
                "metadata": {
                    "primary_system": src.get("primary_system", ""),
                    "origin_gate": src.get("origin_gate", ""),
                    "total_score": src.get("total_score", 0),
                    "status": src.get("status", ""),
                    "timestamp": src.get("timestamp", 0),
                },
                "distance": 1.0 - hit.get("_score", 0),
            })
        return results

    def retrieve_as_context(
        self, question: str, n_results: int = DEFAULT_N_RESULTS
    ) -> str:
        """Retrieve and format as context string for the reasoning engine."""
        results = self.retrieve(question, n_results)
        if not results:
            return ""

        parts = []
        for i, r in enumerate(results, 1):
            dist = r["distance"]
            dist_str = f"{dist:.4f}" if dist is not None else "N/A"
            parts.append(f"--- Prior Verdict {i} (relevance distance: {dist_str}) ---")
            parts.append(r["document"])
            parts.append(f"Score: {r['metadata'].get('total_score', 'N/A')}")
            parts.append(f"Status: {r['metadata'].get('status', 'N/A')}")
            parts.append("")
        return "\n".join(parts)

    def get_verdict_by_id(self, verdict_id: str) -> Optional[dict]:
        """Load a verdict by ID."""
        try:
            doc = self._es.get(index=self._index, id=verdict_id)
            return doc["_source"]
        except NotFoundError:
            return None

    def update_status(
        self,
        verdict_id: str,
        new_status: str,
        corrected_verdict: Optional[Verdict] = None,
    ) -> bool:
        """Update a verdict's status."""
        try:
            self._es.get(index=self._index, id=verdict_id)
        except NotFoundError:
            return False

        if corrected_verdict:
            self.store(corrected_verdict, status="corrected")
            self._es.update(
                index=self._index, id=verdict_id,
                body={"doc": {"status": "superseded"}},
                refresh="wait_for",
            )
        elif new_status == "rejected":
            self._es.update(
                index=self._index, id=verdict_id,
                body={"doc": {"status": "rejected"}},
                refresh="wait_for",
            )
        else:
            update_doc: dict = {"status": new_status}
            # Re-embed if transitioning to an indexed status
            if new_status in ("approved", "corrected") and self._embed_fn:
                src = self.get_verdict_by_id(verdict_id)
                if src:
                    text = (
                        f"Question: {src.get('question', '')}\n"
                        f"Reasoning: {src.get('revised_reasoning', '')}\n"
                        f"Judgment: {src.get('final_judgment', '')}"
                    )
                    update_doc["embedding"] = self._embed_fn(text)

            self._es.update(
                index=self._index, id=verdict_id,
                body={"doc": update_doc},
                refresh="wait_for",
            )

        return True

    def stats(self) -> dict:
        """Return verdict store statistics."""
        total = self._es.count(index=self._index)["count"]
        body = {
            "size": 0,
            "aggs": {"by_status": {"terms": {"field": "status", "size": 20}}},
        }
        resp = self._es.search(index=self._index, body=body)
        by_status = {
            b["key"]: b["doc_count"]
            for b in resp["aggregations"]["by_status"]["buckets"]
        }
        return {"total_indexed": total, "total_files": total, "by_status": by_status}
