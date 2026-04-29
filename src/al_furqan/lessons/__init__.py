"""Al-Furqan Lesson Processing.

Subpackage providing transcript cleaning, enrichment, and transcription.
All modules use standard Python imports — no sys.path hacks.

Modules:
    text_utils       — shared Arabic text utilities (normalize, timestamps, ordinals)
    clean_transcripts — YouTube transcript → structured JSON
    enrich_lessons   — lesson enrichment via ES phrase_match
    transcriber      — Whisper audio → transcript JSON
"""
