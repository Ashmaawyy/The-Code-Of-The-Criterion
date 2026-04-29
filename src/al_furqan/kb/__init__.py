"""Al-Furqan Knowledge Base Layer — Elasticsearch-backed."""

from al_furqan.kb.es.retriever import (
    ESUnifiedRetriever as UnifiedRetriever,
    KnowledgeContext,
    RetrievalConfig,
    RetrievalResult,
    Source,
)
from al_furqan.kb.es.collections import (
    QuranCollection,
    QuranVerse,
    HadithCollection,
    Hadith,
)

__all__ = [
    "UnifiedRetriever",
    "KnowledgeContext",
    "RetrievalConfig",
    "RetrievalResult",
    "Source",
    "QuranCollection",
    "QuranVerse",
    "HadithCollection",
    "Hadith",
]
