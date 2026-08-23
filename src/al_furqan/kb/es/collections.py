"""Elasticsearch-backed collection classes for Quran, Hadith, and Fiqh.

Drop-in replacements for the ChromaDB-backed collections in
``kb/collections/``.  They expose the same public methods (``search``,
``get_verse``, ``get_context``, ``get_hadith``) so the rest of the
application code — retriever, API routers, tafsir pipeline — can switch
backends by changing a single import.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from elasticsearch import Elasticsearch, NotFoundError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses — re-exported from the original modules for convenience
# ---------------------------------------------------------------------------


@dataclass
class QuranVerse:  # pylint: disable=too-many-instance-attributes
    """A single Quran verse with metadata."""

    surah: int
    ayah: int
    text_ar: str
    text_en: str
    juz: int = 0
    page: int = 0
    topics: list[str] = field(default_factory=list)
    surah_name_ar: str = ""
    surah_name_en: str = ""
    revelation_type: str = ""


@dataclass
class Hadith:
    """A single hadith with metadata."""

    collection_name: str
    number: int
    text_ar: str
    text_en: str
    narrator: str = ""
    grading: str = "sahih"
    topics: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# QuranCollection (ES)
# ---------------------------------------------------------------------------


class QuranCollection:
    """Elasticsearch-backed Quran verse collection.

    Supports semantic search (knn on dense_vector), phrase search
    (match_phrase on arabic_furqan analyzer), and exact lookups.
    """

    def __init__(self, es: Elasticsearch, index: str = "furqan_quran") -> None:
        self._es = es
        self._index = index

    @property
    def count(self) -> int:
        return self._es.count(index=self._index)["count"]

    def search(self, query: str, limit: int = 5) -> list[QuranVerse]:
        """Search verses by text. Uses match_phrase for Arabic, multi_match as fallback."""
        body = {
            "query": {
                "bool": {
                    "should": [
                        {"match_phrase": {"text_ar": {"query": query, "boost": 3}}},
                        {"match": {"text_ar": {"query": query, "boost": 2}}},
                        {"match": {"text_en": {"query": query, "boost": 1}}},
                    ],
                },
            },
            "size": limit,
        }
        resp = self._es.search(index=self._index, body=body)
        return [self._hit_to_verse(h) for h in resp["hits"]["hits"]]

    def search_semantic(
        self, embedding: list[float], limit: int = 5
    ) -> list[QuranVerse]:
        """Search by vector similarity (knn)."""
        body = {
            "knn": {
                "field": "embedding",
                "query_vector": embedding,
                "k": limit,
                "num_candidates": limit * 10,
            },
        }
        resp = self._es.search(index=self._index, body=body)
        return [self._hit_to_verse(h) for h in resp["hits"]["hits"]]

    def get_verse(self, surah: int, ayah: int) -> QuranVerse | None:
        """Retrieve a specific verse by surah:ayah."""
        try:
            doc = self._es.get(index=self._index, id=f"{surah}:{ayah}")
            return self._source_to_verse(doc["_source"])
        except NotFoundError:
            return None

    def get_context(self, surah: int, ayah: int, window: int = 2) -> list[QuranVerse]:
        """Get a verse with surrounding context."""
        verses = []
        for offset in range(-window, window + 1):
            target_ayah = ayah + offset
            if target_ayah < 1:
                continue
            v = self.get_verse(surah, target_ayah)
            if v:
                verses.append(v)
        return verses

    def get_by_surah(self, surah: int, limit: int = 300) -> list[QuranVerse]:
        """Get all verses for a surah."""
        body = {
            "query": {"term": {"surah": surah}},
            "sort": [{"ayah": "asc"}],
            "size": limit,
        }
        resp = self._es.search(index=self._index, body=body)
        return [self._hit_to_verse(h) for h in resp["hits"]["hits"]]

    def phrase_match(self, text: str, limit: int = 20) -> list[QuranVerse]:
        """Find verses whose Arabic text appears as a consecutive phrase.

        This replaces the Python sliding-window matching from enrich_lessons.py.
        The arabic_furqan analyzer handles normalization at index time.
        """
        body = {
            "query": {"match_phrase": {"text_ar": {"query": text, "slop": 0}}},
            "size": limit,
        }
        resp = self._es.search(index=self._index, body=body)
        return [self._hit_to_verse(h) for h in resp["hits"]["hits"]]

    @staticmethod
    def _hit_to_verse(hit: dict) -> QuranVerse:
        return QuranCollection._source_to_verse(hit["_source"])

    @staticmethod
    def _source_to_verse(src: dict) -> QuranVerse:
        return QuranVerse(
            surah=src["surah"],
            ayah=src["ayah"],
            text_ar=src.get("text_ar", ""),
            text_en=src.get("text_en", ""),
            juz=src.get("juz", 0),
            page=src.get("page", 0),
            topics=src.get("topics", []),
            surah_name_ar=src.get("surah_name_ar", ""),
            surah_name_en=src.get("surah_name_en", ""),
            revelation_type=src.get("revelation_type", ""),
        )


# ---------------------------------------------------------------------------
# HadithCollection (ES)
# ---------------------------------------------------------------------------


class HadithCollection:
    """Elasticsearch-backed Hadith collection."""

    VALID_GRADINGS = ("sahih", "hasan", "daif")

    def __init__(self, es: Elasticsearch, index: str = "furqan_hadith") -> None:
        self._es = es
        self._index = index

    @property
    def count(self) -> int:
        return self._es.count(index=self._index)["count"]

    def search(
        self,
        query: str,
        limit: int = 5,
        grading_filter: str | None = None,
    ) -> list[Hadith]:
        """Search hadith by text, optionally filtering by grading."""
        must = []
        should = [
            {"match_phrase": {"text_ar": {"query": query, "boost": 3}}},
            {"match": {"text_ar": {"query": query, "boost": 2}}},
            {"match": {"text_en": {"query": query, "boost": 1}}},
        ]

        if grading_filter and grading_filter in self.VALID_GRADINGS:
            must.append({"term": {"grading": grading_filter}})

        body = {
            "query": {
                "bool": {"must": must, "should": should, "minimum_should_match": 1},
            },
            "size": limit,
        }
        resp = self._es.search(index=self._index, body=body)
        return [self._hit_to_hadith(h) for h in resp["hits"]["hits"]]

    def search_semantic(self, embedding: list[float], limit: int = 5) -> list[Hadith]:
        """Search by vector similarity."""
        body = {
            "knn": {
                "field": "embedding",
                "query_vector": embedding,
                "k": limit,
                "num_candidates": limit * 10,
            },
        }
        resp = self._es.search(index=self._index, body=body)
        return [self._hit_to_hadith(h) for h in resp["hits"]["hits"]]

    def get_hadith(self, collection_name: str, number: int) -> Hadith | None:
        """Retrieve a specific hadith."""
        try:
            doc = self._es.get(index=self._index, id=f"{collection_name}:{number}")
            return self._source_to_hadith(doc["_source"])
        except NotFoundError:
            return None

    def phrase_match(self, text: str, limit: int = 20) -> list[Hadith]:
        """Find hadith whose text appears as a consecutive phrase."""
        body = {
            "query": {"match_phrase": {"text_ar": {"query": text, "slop": 0}}},
            "size": limit,
        }
        resp = self._es.search(index=self._index, body=body)
        return [self._hit_to_hadith(h) for h in resp["hits"]["hits"]]

    @staticmethod
    def _hit_to_hadith(hit: dict) -> Hadith:
        return HadithCollection._source_to_hadith(hit["_source"])

    @staticmethod
    def _source_to_hadith(src: dict) -> Hadith:
        topics = src.get("topics", [])
        if isinstance(topics, str):
            topics = [t.strip() for t in topics.split(",") if t.strip()]
        return Hadith(
            collection_name=src.get("collection_name", ""),
            number=src.get("number", 0),
            text_ar=src.get("text_ar", ""),
            text_en=src.get("text_en", ""),
            narrator=src.get("narrator", ""),
            grading=src.get("grading", ""),
            topics=topics,
        )
