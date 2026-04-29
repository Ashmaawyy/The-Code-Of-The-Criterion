"""Elasticsearch-backed Unified Retriever.

Searches across the ES quran and hadith indices using text and phrase
queries.  All dataclasses (Source, RetrievalResult, etc.) are defined
here as the canonical location.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from elasticsearch import Elasticsearch

from al_furqan.kb.es.collections import (
    QuranCollection,
    HadithCollection,
)


# ---------------------------------------------------------------------------
# Retriever dataclasses (canonical location)
# ---------------------------------------------------------------------------

class Source(str, Enum):
    """Knowledge source type."""
    QURAN = "quran"
    HADITH = "hadith"
    FIQH = "fiqh"


@dataclass
class RetrievalResult:
    """A single retrieval result from any collection."""
    source: Source
    content_ar: str
    content_en: str
    reference: str
    metadata: dict = field(default_factory=dict)


@dataclass
class RetrievalConfig:
    """Configuration for retrieval."""
    sources: list[Source] = field(
        default_factory=lambda: [Source.QURAN, Source.HADITH]
    )
    limit_per_source: int = 3
    hadith_grading_filter: Optional[str] = None


@dataclass
class KnowledgeContext:
    """Aggregated knowledge context ready for engine consumption."""
    results: list[RetrievalResult]
    formatted_text: str
    query: str
    sources_searched: list[Source]

logger = logging.getLogger(__name__)


class ESUnifiedRetriever:
    """Searches across all ES-backed KB collections and merges results.

    This is the ES equivalent of ``kb/retriever.py:UnifiedRetriever``.
    It accepts the same ``RetrievalConfig`` and returns the same
    ``KnowledgeContext`` dataclass, so all downstream code (engine,
    API routers, tafsir pipeline) works without changes.
    """

    def __init__(
        self,
        es: Elasticsearch,
        quran_index: str = "furqan_quran",
        hadith_index: str = "furqan_hadith",
    ) -> None:
        self._quran = QuranCollection(es, index=quran_index)
        self._hadith = HadithCollection(es, index=hadith_index)

    def retrieve(
        self,
        query: str,
        config: Optional[RetrievalConfig] = None,
    ) -> KnowledgeContext:
        """Search all configured collections and return merged results."""
        if config is None:
            config = RetrievalConfig()

        all_results: list[RetrievalResult] = []
        sources_searched: list[Source] = []

        # Search Quran
        if Source.QURAN in config.sources:
            sources_searched.append(Source.QURAN)
            try:
                verses = self._quran.search(query, limit=config.limit_per_source)
                for v in verses:
                    all_results.append(
                        RetrievalResult(
                            source=Source.QURAN,
                            content_ar=v.text_ar,
                            content_en=v.text_en,
                            reference=f"Quran {v.surah}:{v.ayah}",
                            metadata={
                                "surah": v.surah,
                                "ayah": v.ayah,
                                "surah_name_en": v.surah_name_en,
                                "juz": v.juz,
                            },
                        )
                    )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Quran search failed: %s", e)

        # Search Hadith
        if Source.HADITH in config.sources:
            sources_searched.append(Source.HADITH)
            try:
                hadith_results = self._hadith.search(
                    query,
                    limit=config.limit_per_source,
                    grading_filter=config.hadith_grading_filter,
                )
                for h in hadith_results:
                    all_results.append(
                        RetrievalResult(
                            source=Source.HADITH,
                            content_ar=h.text_ar,
                            content_en=h.text_en,
                            reference=f"{h.collection_name.capitalize()} #{h.number}",
                            metadata={
                                "collection": h.collection_name,
                                "number": h.number,
                                "narrator": h.narrator,
                                "grading": h.grading,
                            },
                        )
                    )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Hadith search failed: %s", e)

        # Deduplicate by reference
        seen: set[str] = set()
        deduped: list[RetrievalResult] = []
        for r in all_results:
            if r.reference not in seen:
                seen.add(r.reference)
                deduped.append(r)

        formatted = self._format_results(deduped)

        return KnowledgeContext(
            results=deduped,
            formatted_text=formatted,
            query=query,
            sources_searched=sources_searched,
        )

    @staticmethod
    def _format_results(results: list[RetrievalResult]) -> str:
        """Format results into text for engine consumption."""
        if not results:
            return "No relevant knowledge found."

        sections: list[str] = []

        quran = [r for r in results if r.source == Source.QURAN]
        hadith = [r for r in results if r.source == Source.HADITH]

        if quran:
            lines = ["=== Quran Evidence ==="]
            for r in quran:
                lines.append(f"[{r.reference}]")
                lines.append(f"  Arabic: {r.content_ar}")
                lines.append(f"  English: {r.content_en}")
            sections.append("\n".join(lines))

        if hadith:
            lines = ["=== Hadith Evidence ==="]
            for r in hadith:
                grading = r.metadata.get("grading", "")
                narrator = r.metadata.get("narrator", "")
                lines.append(f"[{r.reference}] ({grading}) — Narrated by {narrator}")
                lines.append(f"  Arabic: {r.content_ar}")
                lines.append(f"  English: {r.content_en}")
            sections.append("\n".join(lines))

        return "\n\n".join(sections)
