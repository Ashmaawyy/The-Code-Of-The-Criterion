"""
LLM-based Relationship Extractor for the Knowledge Graph pipeline.

Takes transcript chunks and extracts scholarly relationships using the
existing LLM layer. All extracted edges are proposed (status="pending")
and require human review before entering the KG.
"""

import json
import re
from dataclasses import dataclass

from ...providers.llm_layer import LLMConfig, LLMProvider, create_llm
from ..ingestion.models import ProposedEdge
from ..ingestion.transcript_chunker import TranscriptChunk, format_chunk_timestamp

EXTRACTION_PROMPT_TEMPLATE = """You are an Islamic knowledge extraction assistant analyzing a scholarly lecture (دروس علمية) on Surah Al-Anam by Sheikh Ahmad Al-Sayed.  # pylint: disable=line-too-long

## CRITICAL STRUCTURE RULES:

The Knowledge Graph is built around CENTRAL VERSES. The sheikh explains one verse at a time (the "center"), and while explaining it, he references other verses, hadith, and concepts.

Your job is to identify:
1. **The CENTRAL VERSE** — the verse the sheikh is currently explaining in this chunk
2. **LINKED VERSES** — other verses he mentions WHILE explaining the central verse, with his words connecting them
3. **LINKED HADITH** — hadith he cites while explaining, with his connecting words
4. **GENERAL TAFSIR** — the sheikh's explanation that is NOT linked to a specific other verse or hadith

## STRUCTURE:

```
Central Verse (الآية المركزية)
├── LINKED_VERSE → other verse + sheikh's connecting words
├── LINKED_HADITH → hadith + sheikh's connecting words
├── HAS_TAFSIR → sheikh's general explanation of this verse
└── NEXT_VERSE → new central verse (only if sheikh EXPLICITLY moves to next verse)
```

## CRITICAL RULES FOR CENTRAL VERSE:
1. The sheikh organizes his tafsir BY TOPIC, not by verse number. Multiple consecutive verses about the same topic are grouped together under ONE central verse.
2. A NEW central verse appears when the sheikh transitions to a NEW TOPIC/THEME. The verse that opens the new topic becomes the new central verse.
3. Example: Verses 6:1-4 all discuss the same introductory theme (Allah's creation, knowledge, and the disbelievers' rejection) → they share one central verse (6:1). When the sheikh moves to the topic of "أنباء ما كانوا به يستهزئون" → verse 6:5 becomes the new central verse because it opens a new theme.
4. The central verse generally follows the surah order, but may SKIP verses that belong to the same topic group. E.g., 6:1 (covers 1-4) → 6:5 → next topic verse. It does NOT jump far (e.g., from 6:5 to 6:121). If the sheikh mentions a distant verse like 6:121 while explaining 6:5, that is a LINKED_VERSE — he is connecting it to the current topic, NOT starting a new central verse.
5. Signals of a topic change (= new central verse):
   - The sheikh recites a NEW verse and begins explaining it as a new subject
   - A clear shift in the discussion theme (e.g., from "السنة الإلهية" to "تشريعات الأنعام")
   - Phrases like "ثم ننتقل" / "والآن مع" / "ثم يقول الله" followed by in-depth explanation
6. DISTINGUISH between "citing a verse briefly as evidence for the current topic" (= LINKED_VERSE) vs "beginning a new topic centered on a new verse" (= new CENTRAL VERSE).
7. If the sheikh mentions verse 6:80 while explaining the topic of verse 6:5, that is a LINKED_VERSE, NOT a new central verse.
8. When in doubt, keep the same central verse. Do NOT change it.

## OTHER RULES:
9. ONLY extract what the SCHOLAR EXPLICITLY says. Do NOT infer.
10. LINKED_VERSE and LINKED_HADITH must include the sheikh's EXACT WORDS explaining the connection.
11. HAS_TAFSIR captures the sheikh's explanation that doesn't reference other specific verses/hadith.
12. Use surah:ayah format (e.g., "6:1", "2:255").
13. Be conservative — fewer accurate edges are better than many speculative ones.
14. If previous chunk's central verse is provided, continue from there unless the sheikh clearly moved to a new topic with a new central verse.

{previous_context}

TRANSCRIPT CHUNK (from {lesson_reference}, {timestamp}):
---
{chunk_text}
---

Respond in VALID JSON:
{{
  "central_verse": "6:X",
  "central_verse_changed": true/false,
  "relationships": [
    {{
      "source_node": "6:X",
      "target_node": "target verse/hadith/concept",
      "edge_type": "LINKED_VERSE/LINKED_HADITH/HAS_TAFSIR/NEXT_VERSE",
      "sheikh_words": "exact or near-exact quote from the sheikh connecting them",
      "reasoning": "why this relationship exists",
      "confidence": 0.0-1.0
    }}
  ],
  "verse_references": ["6:1", "2:255"],
  "topics": ["توحيد"],
  "hadith_references": ["description"]
}}

If no clear relationships: {{"central_verse": "", "central_verse_changed": false, "relationships": [], "verse_references": [], "topics": [], "hadith_references": []}}
"""


@dataclass
class ExtractionResult:
    """Result of extracting relationships from a chunk."""

    chunk: TranscriptChunk
    edges: list[ProposedEdge]
    verse_references: list[str]
    topics: list[str]
    hadith_references: list[str]
    raw_llm_response: str


def _parse_llm_response(response: str) -> dict:
    """Parse LLM JSON response, handling common issues."""
    # Try to find JSON in the response
    response = response.strip()

    # Try direct parse first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try to find JSON block in markdown code fences
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find any JSON object
    brace_start = response.find("{")
    brace_end = response.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        try:
            return json.loads(response[brace_start : brace_end + 1])
        except json.JSONDecodeError:
            pass

    # Return empty result
    return {
        "relationships": [],
        "verse_references": [],
        "topics": [],
        "hadith_references": [],
    }


def extract_relationships(  # pylint: disable=too-many-arguments, too-many-locals, too-many-positional-arguments
    chunk: TranscriptChunk,
    llm: LLMProvider,
    lesson_id: str = "lesson_01",
    lesson_reference: str = "مدارسة سورة الأنعام — الحلقة 01",
    provenance: str = "sheikh_ahmad_alsayed",
    provenance_type: str = "scholarly_lecture",
) -> ExtractionResult:
    """
    Extract relationships from a transcript chunk using the LLM.

    Args:
        chunk: The transcript chunk to analyze.
        llm: The LLM provider to use for extraction.
        lesson_id: Identifier for the lesson.
        lesson_reference: Human-readable lesson reference.
        provenance: Source attribution.
        provenance_type: Type of source.

    Returns:
        ExtractionResult with proposed edges and metadata.
    """
    timestamp = format_chunk_timestamp(chunk)

    # Build previous context for continuity
    previous_context = ""
    if hasattr(chunk, "_previous_central_verse") and chunk._previous_central_verse:  # pylint: disable=protected-access
        previous_context = f"PREVIOUS CHUNK'S CENTRAL VERSE: {chunk._previous_central_verse}\nContinue from this verse unless the sheikh clearly moved to the next verse."  # pylint: disable=line-too-long, protected-access

    prompt = EXTRACTION_PROMPT_TEMPLATE.format(
        lesson_reference=lesson_reference,
        timestamp=timestamp,
        chunk_text=chunk.text,
        previous_context=previous_context,
    )

    # Call the LLM
    raw_response = llm(prompt)

    # Parse the response
    parsed = _parse_llm_response(raw_response)

    relationships = parsed.get("relationships", [])
    verse_refs = parsed.get("verse_references", [])
    topics = parsed.get("topics", [])
    hadith_refs = parsed.get("hadith_references", [])
    central_verse = parsed.get("central_verse", "")

    # Convert relationships to ProposedEdge objects
    edges: list[ProposedEdge] = []
    for rel in relationships:
        if not isinstance(rel, dict):
            continue

        source = rel.get("source_node", "").strip()
        target = rel.get("target_node", "").strip()
        edge_type = rel.get("edge_type", "").strip()

        if not source or not target or not edge_type:
            continue

        # Include sheikh's connecting words in the reasoning
        sheikh_words = rel.get("sheikh_words", "")
        reasoning = rel.get("reasoning", "")
        if sheikh_words and sheikh_words not in reasoning:
            reasoning = f'قال الشيخ: "{sheikh_words}" — {reasoning}'

        edge = ProposedEdge(
            id=ProposedEdge.generate_id(),
            lesson_id=lesson_id,
            source_node=source,
            target_node=target,
            edge_type=edge_type,
            provenance=provenance,
            provenance_type=provenance_type,
            reference=f"{lesson_reference}, {timestamp}",
            timestamp_start=str(chunk.start_time),
            timestamp_end=str(chunk.end_time),
            transcript_chunk=chunk.text[:500],  # Truncate for storage
            llm_reasoning=reasoning,
            llm_confidence=float(rel.get("confidence", 0.5)),
            status="pending",
        )
        edges.append(edge)

    result = ExtractionResult(
        chunk=chunk,
        edges=edges,
        verse_references=verse_refs,
        topics=topics,
        hadith_references=hadith_refs,
        raw_llm_response=raw_response,
    )
    # Store central verse for next chunk continuity
    result.central_verse = central_verse  # pylint: disable=attribute-defined-outside-init
    return result


def create_extraction_llm(
    api_key: str,
    model_name: str = "qwen3-235b-a22b",
) -> LLMProvider:
    """Create an LLM provider configured for relationship extraction."""
    config = LLMConfig(
        provider="dashscope",
        model_name=model_name,
        api_key=api_key,
        temperature=0.1,
        max_tokens=4096,
        timeout=120,
    )
    return create_llm(config)
