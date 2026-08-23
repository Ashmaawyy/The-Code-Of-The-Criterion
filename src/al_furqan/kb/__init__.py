"""Al-Furqan Knowledge Base Layer — Elasticsearch-backed."""

from al_furqan.kb.es.collections import (
    Hadith,
    HadithCollection,
    QuranCollection,
    QuranVerse,
)
from al_furqan.kb.es.retriever import (
    ESUnifiedRetriever as UnifiedRetriever,
)
from al_furqan.kb.es.retriever import (
    KnowledgeContext,
    RetrievalConfig,
    RetrievalResult,
    Source,
)

__all__ = [
    "Hadith",
    "HadithCollection",
    "KnowledgeContext",
    "QuranCollection",
    "QuranVerse",
    "RetrievalConfig",
    "RetrievalResult",
    "Source",
    "UnifiedRetriever",
]
