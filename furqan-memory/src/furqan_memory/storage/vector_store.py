"""
Embedded vector search for Furqan Memory using ChromaDB.

Provides semantic similarity search over stored verdicts and patterns.
"""

from __future__ import annotations

import json
import uuid

import chromadb


class MemoryVectorSearch:
    """Semantic search over stored verdicts and patterns using ChromaDB."""

    def __init__(self, persist_dir: str | None = None, collection_prefix: str = "memory"):
        """Initialize vector search.

        Args:
            persist_dir: Path for persistent storage. None = ephemeral (for tests).
            collection_prefix: Prefix for collection names (for test isolation).
        """
        if persist_dir:
            self.client = chromadb.PersistentClient(path=persist_dir)
        else:
            self.client = chromadb.EphemeralClient()

        # Use unique collection names to ensure isolation between instances
        suffix = uuid.uuid4().hex[:8] if not persist_dir else ""
        self.verdicts = self.client.get_or_create_collection(
            name=f"{collection_prefix}_verdicts_{suffix}" if suffix else f"{collection_prefix}_verdicts",  # pylint: disable=line-too-long
            metadata={"hnsw:space": "cosine"},
        )
        self.patterns = self.client.get_or_create_collection(
            name=f"{collection_prefix}_patterns_{suffix}" if suffix else f"{collection_prefix}_patterns",  # pylint: disable=line-too-long
            metadata={"hnsw:space": "cosine"},
        )

    def add_verdict(self, id: str, question: str, metadata: dict | None = None) -> None:  # pylint: disable=redefined-builtin
        """Add a verdict to the vector store.

        Args:
            id: Unique verdict ID.
            question: The question text (used as the document for embedding).
            metadata: Additional metadata to store alongside.
        """
        safe_meta = self._safe_metadata(metadata or {})
        kwargs = {"ids": [id], "documents": [question]}
        if safe_meta:
            kwargs["metadatas"] = [safe_meta]
        self.verdicts.upsert(**kwargs)

    def add_pattern(self, id: str, rule: str, metadata: dict | None = None) -> None:  # pylint: disable=redefined-builtin
        """Add a pattern to the vector store.

        Args:
            id: Unique pattern ID.
            rule: The pattern rule text (used as the document for embedding).
            metadata: Additional metadata to store alongside.
        """
        safe_meta = self._safe_metadata(metadata or {})
        kwargs = {"ids": [id], "documents": [rule]}
        if safe_meta:
            kwargs["metadatas"] = [safe_meta]
        self.patterns.upsert(**kwargs)

    def search_verdicts(self, query: str, limit: int = 5) -> list[dict]:
        """Search verdicts by semantic similarity.

        Returns list of dicts with keys: id, score, question, metadata.
        """
        results = self.verdicts.query(
            query_texts=[query],
            n_results=min(limit, max(self.verdicts.count(), 1)),
        )
        return self._format_results(results)

    def search_patterns(self, query: str, limit: int = 5) -> list[dict]:
        """Search patterns by semantic similarity.

        Returns list of dicts with keys: id, score, rule, metadata.
        """
        count = self.patterns.count()
        if count == 0:
            return []
        results = self.patterns.query(
            query_texts=[query],
            n_results=min(limit, count),
        )
        return self._format_results(results)

    @staticmethod
    def _format_results(results: dict) -> list[dict]:
        """Convert ChromaDB query results to a simple list of dicts."""
        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        formatted = []
        ids = results["ids"][0]
        documents = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for i, doc_id in enumerate(ids):
            # ChromaDB returns distances (lower = more similar for cosine)
            # Convert to similarity score: 1 - distance (for cosine)
            distance = distances[i] if i < len(distances) else 1.0
            score = max(0.0, 1.0 - distance)
            formatted.append({
                "id": doc_id,
                "score": score,
                "document": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
            })
        return formatted

    @staticmethod
    def _safe_metadata(metadata: dict) -> dict:
        """Ensure metadata values are ChromaDB-compatible (str, int, float, bool)."""
        safe = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                safe[k] = v
            elif v is None:
                continue
            else:
                safe[k] = json.dumps(v, ensure_ascii=False)
        return safe
