"""Extract ayah→sira_event edges from the sira database."""

from __future__ import annotations

import logging

from training.pipeline.extractors.types import ExtractorResult, add_edge

logger = logging.getLogger(__name__)


def extract(**kwargs) -> ExtractorResult:
    result: ExtractorResult = {}

    from training.pipeline.sira_db.db import EVENTS

    count = 0
    for event in EVENTS:
        verses = event.get("verses") or []
        if not verses:
            continue

        event_id = event.get("id", "")
        tags = event.get("tags") or {}

        edge_data = {
            "event_id": event_id,
            "order": event.get("order"),
            "year_ah": event.get("year_ah"),
            "period": event.get("period", ""),
            "title_ar": event.get("title_ar", ""),
            "title_en": event.get("title_en", ""),
            "location": event.get("location", ""),
            "description_ar": event.get("description_ar", ""),
            "lesson_ar": event.get("lesson_ar", ""),
            "response_type": event.get("response_type", ""),
            "pressure_type": tags.get("pressure_type", []),
            "parties": tags.get("parties", []),
            "stakes": tags.get("stakes", []),
            "response_category": tags.get("response_category", ""),
            "principle_class": tags.get("principle_class", ""),
            "polarity": tags.get("polarity", []),
        }

        for vk in verses:
            add_edge(result, vk, {
                "edge_type": "sira_event",
                "target_id": f"sira:{event_id}",
                "weight": 1.0,
                "confidence": 1.0,
                "provenance": "sira_db",
                "data": edge_data,
            })
            count += 1

    logger.info("sira: %d edges across %d verses", count, len(result))
    return result
