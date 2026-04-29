"""Edge extractors for the verse-centric knowledge graph."""

from training.pipeline.extractors.tafsir_edges import extract as extract_tafsir
from training.pipeline.extractors.transition_edges import extract as extract_transitions
from training.pipeline.extractors.sira_edges import extract as extract_sira
from training.pipeline.extractors.lesson_edges import extract as extract_lessons
from training.pipeline.extractors.crossref_edges import extract as extract_crossrefs
from training.pipeline.extractors.hadith_edges import extract as extract_hadith

ALL_EXTRACTORS = {
    "tafsir": extract_tafsir,
    "transition": extract_transitions,
    "sira": extract_sira,
    "lesson": extract_lessons,
    "crossref": extract_crossrefs,
    "hadith": extract_hadith,
}
