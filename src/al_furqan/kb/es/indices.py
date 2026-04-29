"""Elasticsearch index definitions for all Al-Furqan collections.

Each index is defined as a dict of {settings, mappings} ready to be passed
to ``es.indices.create()``.  The ``arabic_furqan`` analyzer from
``analyzers.py`` is injected into settings at creation time.
"""

from al_furqan.kb.es.analyzers import ANALYSIS_SETTINGS

# Embedding dimensions — matches the MiniLM model used by kb/embeddings.py.
EMBEDDING_DIMS = 384


def _ar_text_field() -> dict:
    """Standard Arabic text field with raw keyword sub-field."""
    return {
        "type": "text",
        "analyzer": "arabic_furqan",
        "fields": {"raw": {"type": "keyword", "ignore_above": 5000}},
    }


def _en_text_field() -> dict:
    """Standard English text field."""
    return {"type": "text", "analyzer": "english"}


def _embedding_field() -> dict:
    """Dense vector field for cosine similarity search."""
    return {
        "type": "dense_vector",
        "dims": EMBEDDING_DIMS,
        "index": True,
        "similarity": "cosine",
    }


# ---------------------------------------------------------------------------
# Index: furqan_quran
# ---------------------------------------------------------------------------

QURAN_INDEX = {
    "settings": {**ANALYSIS_SETTINGS, "number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "properties": {
            "surah": {"type": "integer"},
            "ayah": {"type": "integer"},
            "verse_key": {"type": "keyword"},
            "surah_name_ar": {"type": "keyword"},
            "surah_name_en": {"type": "keyword"},
            "text_ar": _ar_text_field(),
            "text_en": _en_text_field(),
            "juz": {"type": "integer"},
            "page": {"type": "integer"},
            "revelation_type": {"type": "keyword"},
            "topics": {"type": "keyword"},
            "embedding": _embedding_field(),
        },
    },
}


# ---------------------------------------------------------------------------
# Index: furqan_hadith
# ---------------------------------------------------------------------------

HADITH_INDEX = {
    "settings": {**ANALYSIS_SETTINGS, "number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "properties": {
            "collection_name": {"type": "keyword"},
            "number": {"type": "integer"},
            "hadith_key": {"type": "keyword"},
            "text_ar": _ar_text_field(),
            "text_en": _en_text_field(),
            "narrator": {"type": "keyword"},
            "grading": {"type": "keyword"},
            "topics": {"type": "keyword"},
            "embedding": _embedding_field(),
        },
    },
}


# ---------------------------------------------------------------------------
# Index: furqan_graph
# ---------------------------------------------------------------------------

GRAPH_INDEX = {
    "settings": {**ANALYSIS_SETTINGS, "number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "properties": {
            "source": {"type": "keyword"},
            "target": {"type": "keyword"},
            "edge_type": {"type": "keyword"},
            "weight": {"type": "float"},
            "provenance": {"type": "keyword"},
            "provenance_type": {"type": "keyword"},
            "reference": {"type": "text", "analyzer": "arabic_furqan"},
            "verified_by": {"type": "keyword"},
            "confidence": {"type": "float"},
            "metadata": {"type": "object", "enabled": False},
        },
    },
}


# ---------------------------------------------------------------------------
# Index: furqan_lessons
# ---------------------------------------------------------------------------

LESSONS_INDEX = {
    "settings": {**ANALYSIS_SETTINGS, "number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "properties": {
            "lesson_number": {"type": "integer"},
            "surah": {"type": "keyword"},
            "title": {"type": "keyword"},
            "total_chapters": {"type": "integer"},
            "chapters": {
                "type": "nested",
                "properties": {
                    "chapter_number": {"type": "integer"},
                    "title": {"type": "text", "analyzer": "arabic_furqan"},
                    "content": _ar_text_field(),
                    "taught_verses": {
                        "type": "nested",
                        "properties": {
                            "verse_key": {"type": "keyword"},
                            "surah": {"type": "integer"},
                            "ayah": {"type": "integer"},
                            "surah_name_ar": {"type": "keyword"},
                            "text_ar": _ar_text_field(),
                            "text_en": _en_text_field(),
                        },
                    },
                    "linked_verses": {
                        "type": "nested",
                        "properties": {
                            "verse_key": {"type": "keyword"},
                            "surah": {"type": "integer"},
                            "ayah": {"type": "integer"},
                            "surah_name_ar": {"type": "keyword"},
                            "text_ar": _ar_text_field(),
                            "text_en": _en_text_field(),
                        },
                    },
                    "mentioned_ahadeeth": {
                        "type": "nested",
                        "properties": {
                            "collection": {"type": "keyword"},
                            "number": {"type": "integer"},
                            "text_ar": _ar_text_field(),
                            "text_en": _en_text_field(),
                        },
                    },
                },
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Index: furqan_verdicts
# ---------------------------------------------------------------------------

VERDICTS_INDEX = {
    "settings": {**ANALYSIS_SETTINGS, "number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "properties": {
            "verdict_id": {"type": "keyword"},
            "question": {"type": "text", "analyzer": "arabic_furqan"},
            "primary_system": {"type": "keyword"},
            "origin_gate": {"type": "keyword"},
            "friction_points": {"type": "text", "analyzer": "arabic_furqan"},
            "revised_reasoning": {"type": "text", "analyzer": "arabic_furqan"},
            "final_judgment": {"type": "text", "analyzer": "arabic_furqan"},
            "total_score": {"type": "float"},
            "passes": {"type": "boolean"},
            "status": {"type": "keyword"},
            "timestamp": {"type": "date"},
            "gate_scores": {
                "type": "nested",
                "properties": {
                    "gate_id": {"type": "keyword"},
                    "score": {"type": "float"},
                    "reasoning": {"type": "text"},
                },
            },
            "embedding": _embedding_field(),
        },
    },
}


# ---------------------------------------------------------------------------
# Index: furqan_feedback
# ---------------------------------------------------------------------------

FEEDBACK_INDEX = {
    "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    "mappings": {
        "properties": {
            "feedback_id": {"type": "keyword"},
            "verdict_id": {"type": "keyword"},
            "reviewer": {"type": "keyword"},
            "rating": {"type": "keyword"},
            "gate_corrections": {"type": "object", "enabled": False},
            "notes": {"type": "text"},
            "timestamp": {"type": "date"},
        },
    },
}


# ---------------------------------------------------------------------------
# Registry — maps logical name → (index suffix, definition)
# ---------------------------------------------------------------------------

INDEX_REGISTRY: dict[str, dict] = {
    "quran": QURAN_INDEX,
    "hadith": HADITH_INDEX,
    "graph": GRAPH_INDEX,
    "lessons": LESSONS_INDEX,
    "verdicts": VERDICTS_INDEX,
    "feedback": FEEDBACK_INDEX,
}


# ---------------------------------------------------------------------------
# Training indices — bulk-loaded from JSONL files by the staging pipeline
# ---------------------------------------------------------------------------

_TRAINING_BASE_SETTINGS = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "refresh_interval": "30s",
    "analysis": {
        "analyzer": {"arabic_furqan": {"type": "arabic"}},
    },
}


GRAPH_EDGES_INDEX: dict = {
    "settings": _TRAINING_BASE_SETTINGS,
    "mappings": {
        "properties": {
            "verse_key": {"type": "keyword"},
            "surah": {"type": "integer"},
            "ayah": {"type": "integer"},
            "revelation_type": {"type": "keyword"},
            "juz": {"type": "integer"},
            "edge_type": {"type": "keyword"},
            "target_id": {"type": "keyword"},
            "weight": {"type": "float"},
            "confidence": {"type": "float"},
            "provenance": {"type": "keyword"},
            "tafsir_book": {"type": "keyword"},
            "tafsir_scholar": {"type": "keyword"},
            "tafsir_era": {"type": "keyword"},
            "collection": {"type": "keyword"},
            "event_id": {"type": "keyword"},
            "period": {"type": "keyword"},
            "transition_type": {"type": "keyword"},
            "smoothness": {"type": "float"},
            "lesson_number": {"type": "integer"},
            "relation": {"type": "keyword"},
        },
    },
}


HISTORY_EVENTS_INDEX: dict = {
    "settings": _TRAINING_BASE_SETTINGS,
    "mappings": {
        "properties": {
            "event_id": {"type": "keyword"},
            "source": {"type": "keyword"},
            "name": {"type": "text", "analyzer": "standard"},
            "year": {"type": "integer"},
            "year_end": {"type": "integer"},
            "period": {"type": "keyword"},
            "country": {"type": "keyword"},
            "event_type": {"type": "keyword"},
            "location": {"type": "text"},
            "edge_count": {"type": "integer"},
            "edges": {"type": "object", "enabled": False},
            "edge_counts": {"type": "object", "enabled": False},
        },
    },
}


# Plan entry shape:
#   {
#       "index":   full ES index name (not prefix-based)
#       "mapping": index definition dict (settings + mappings)
#       "file":    relative path under DATA_TRAINING
#       "flatten": True  → one ES doc per edge  (uses graph flattener)
#                  False → one ES doc per event (uses history flattener)
#   }
TRAINING_INDEX_PLAN: dict[str, dict] = {
    "graph": {
        "index": "furqan_graph_edges",
        "mapping": GRAPH_EDGES_INDEX,
        "file": "quran_graph.jsonl",
        "flatten": True,
    },
    "history": {
        "index": "furqan_history_events",
        "mapping": HISTORY_EVENTS_INDEX,
        "file": "human_history.jsonl",
        "flatten": False,
    },
    "testing_talk_about_history": {
        "index": "furqan_testing_talk_about_history",
        "mapping": HISTORY_EVENTS_INDEX,
        "file": "testing/model_testing_how_people_talk_about_history.jsonl",
        "flatten": False,
    },
}
