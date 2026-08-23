"""ES cache layer — transparent fallback for generators when ES is down.

Provides three capabilities:
  1. `scroll_index(index)` — iterates all docs (tries ES, falls back to cache)
  2. `get_doc(index, doc_id)` — point lookup by ID (tries ES, falls back to cache)
  3. `search_index(index, body)` — filtered search (tries ES, falls back to cache
     with in-memory filtering)

Cache files live in `data_archive/.es_cache/<index_name>.jsonl` and are
created by `es_snapshot.py`. They are gitignored, ephemeral, and rebuildable.

Usage in generators:
    from training.pipeline.es_cache import ESSource

    source = ESSource()  # auto-detects ES vs cache
    for doc in source.scroll("furqan_tafsir_structural"):
        process(doc)

    verse = source.get("furqan_quran", "2:255")
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from al_furqan.paths import ES_CACHE_DIR as CACHE_DIR

logger = logging.getLogger(__name__)
_ES_URL_DEFAULT = "http://localhost:9200"


class ESSource:
    """Unified data source that tries ES first, falls back to local cache.

    The fallback is transparent: generators don't need to know which
    backend they're talking to. A single warning is logged on first
    fallback so the user knows they're running against stale data.
    """

    def __init__(
        self,
        es_url: str | None = None,
        cache_dir: Path = CACHE_DIR,
        force_cache: bool = False,
    ):
        self._cache_dir = cache_dir
        self._es = None
        self._es_available = False
        self._warned_fallback = False
        self._id_caches: dict[str, dict[str, dict]] = {}

        if force_cache:
            logger.info("ESSource: forced cache mode (--offline)")
            return

        # Try to connect to ES
        url = es_url or os.environ.get("ELASTICSEARCH_URL", _ES_URL_DEFAULT)
        try:
            from elasticsearch import Elasticsearch

            es = Elasticsearch(hosts=[url], request_timeout=5)
            if es.ping():
                self._es = es
                self._es_available = True
                info = es.info()
                logger.info(
                    "ESSource: connected to ES %s at %s", info["version"]["number"], url
                )
            else:
                self._warn_fallback("ES ping failed")
        except Exception as e:
            self._warn_fallback(f"ES connection error: {e}")

    def _warn_fallback(self, reason: str) -> None:
        if not self._warned_fallback:
            logger.warning(
                "ESSource: %s — falling back to local cache in %s",
                reason,
                self._cache_dir,
            )
            self._warned_fallback = True

    @property
    def is_live(self) -> bool:
        """True if reading from ES, False if reading from cache."""
        return self._es_available

    # ------------------------------------------------------------------
    # Pattern A: full-scan scroll
    # ------------------------------------------------------------------

    def scroll(
        self,
        index: str,
        sort: list[dict] | None = None,
        source_fields: list[str] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Iterate all docs in an index. Tries ES scroll, falls back to cache.

        Yields `_source` dicts (not the full ES hit envelope).
        """
        if self._es_available:
            yield from self._es_scroll(index, sort, source_fields)
        else:
            yield from self._cache_scroll(index)

    def _es_scroll(
        self,
        index: str,
        sort: list[dict] | None,
        source_fields: list[str] | None,
    ) -> Iterator[dict]:
        body: dict[str, Any] = {"query": {"match_all": {}}}
        if sort:
            body["sort"] = sort
        kwargs: dict[str, Any] = {
            "index": index,
            "body": body,
            "scroll": "5m",
            "size": 500,
        }
        if source_fields:
            kwargs["_source"] = source_fields

        resp = self._es.search(**kwargs)
        scroll_id = resp["_scroll_id"]
        try:
            while True:
                hits = resp["hits"]["hits"]
                if not hits:
                    break
                for hit in hits:
                    yield hit["_source"]
                resp = self._es.scroll(scroll_id=scroll_id, scroll="5m")
        finally:
            try:
                self._es.clear_scroll(scroll_id=scroll_id)
            except Exception:
                pass

    def _cache_scroll(self, index: str) -> Iterator[dict]:
        cache_path = self._cache_dir / f"{index}.jsonl"
        if not cache_path.exists():
            logger.error(
                "Cache file not found: %s — run es_snapshot.py first", cache_path
            )
            return
        with cache_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

    # ------------------------------------------------------------------
    # Pattern B: point lookup by ID
    # ------------------------------------------------------------------

    def get(self, index: str, doc_id: str) -> dict[str, Any] | None:
        """Get a single doc by ID. Tries ES, falls back to cached ID index."""
        if self._es_available:
            return self._es_get(index, doc_id)
        return self._cache_get(index, doc_id)

    def _es_get(self, index: str, doc_id: str) -> dict | None:
        try:
            resp = self._es.get(index=index, id=doc_id)
            return resp["_source"]
        except Exception:
            return None

    def _cache_get(self, index: str, doc_id: str) -> dict | None:
        # Lazy-load the full index into an ID map on first access
        if index not in self._id_caches:
            self._id_caches[index] = self._build_id_cache(index)
        return self._id_caches[index].get(doc_id)

    def _build_id_cache(self, index: str) -> dict[str, dict]:
        """Load a cache file into a {doc_id: _source} dict for point lookups."""
        cache_path = self._cache_dir / f"{index}.jsonl"
        if not cache_path.exists():
            logger.error("Cache file not found for ID lookup: %s", cache_path)
            return {}
        out: dict[str, dict] = {}
        with cache_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Use _id field if present, else try verse_key or _doc_id
                doc_id = doc.pop("_id", None) or doc.get("verse_key") or ""
                if doc_id:
                    out[doc_id] = doc
        logger.info("Built ID cache for %s: %d docs", index, len(out))
        return out

    # ------------------------------------------------------------------
    # Pattern C: filtered search (for complex queries)
    # ------------------------------------------------------------------

    def search(
        self,
        index: str,
        body: dict[str, Any],
        size: int = 500,
    ) -> list[dict[str, Any]]:
        """Run a search query. Tries ES, falls back to full-scan + filter.

        For cache fallback, filtering is best-effort: complex nested
        queries are simplified to returning all docs (the generator
        does its own in-memory filtering anyway).
        """
        if self._es_available:
            return self._es_search(index, body, size)
        # Fallback: return all docs — generators filter in-memory
        logger.debug("Cache fallback for search on %s — returning all docs", index)
        return list(self._cache_scroll(index))

    def _es_search(self, index: str, body: dict, size: int) -> list[dict]:
        resp = self._es.search(index=index, body=body, size=size)
        return [hit["_source"] for hit in resp["hits"]["hits"]]

    # ------------------------------------------------------------------
    # Utility: check if an index exists (in ES or cache)
    # ------------------------------------------------------------------

    def index_exists(self, index: str) -> bool:
        if self._es_available:
            return self._es.indices.exists(index=index)
        return (self._cache_dir / f"{index}.jsonl").exists()

    # ------------------------------------------------------------------
    # Write support (for generators that index results into ES)
    # ------------------------------------------------------------------

    def create_index(self, index: str, body: dict[str, Any]) -> None:
        """Create/recreate an ES index. No-op in cache mode."""
        if not self._es_available:
            logger.warning("Cannot create index %s — ES is down", index)
            return
        if self._es.indices.exists(index=index):
            self._es.indices.delete(index=index)
        self._es.indices.create(index=index, **body)

    def bulk_index(self, actions: list[dict[str, Any]]) -> int:
        """Bulk index actions into ES. Returns count. No-op in cache mode."""
        if not self._es_available:
            logger.warning("Cannot bulk index — ES is down (actions discarded)")
            return 0
        from elasticsearch.helpers import bulk

        success, errors = bulk(self._es, actions, chunk_size=1000, raise_on_error=False)
        if errors:
            logger.warning("%d bulk errors", len(errors))
        return success

    def refresh(self, index: str) -> None:
        if self._es_available:
            self._es.indices.refresh(index=index)
