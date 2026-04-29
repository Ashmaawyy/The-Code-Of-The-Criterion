"""Chronological database of Sira events tied to Quranic verses.

Target: 800 well-attested events with full structural tags. Each event
carries its six-axis structural fingerprint (see schema.py) so the analogy
generator and retrieval layer can match historical precedents against
modern scenarios by structure, not by surface features.

Sources: al-Wahidi's Asbab al-Nuzul, al-Suyuti's Lubab al-Nuqul, Ibn
Hisham's Sira, Ibn Kathir's Bidaya wa Nihaya, al-Tabari's Tarikh.
Conservative selections only — events whose verse linkage is attested
in classical asbab literature.

The EVENTS list is built from multiple topic-scoped modules to keep
each file manageable for review and diffing:
  meccan.py         — Meccan period (early/middle/late)
  medinan_early.py  — Medinan period years 1-3 AH
  medinan_middle.py — Medinan period years 4-6 AH
  medinan_late.py   — Medinan period years 7-11 AH
  asbab.py          — additional asbab al-nuzul by surah
"""

from __future__ import annotations

from training.pipeline.sira_db.schema import REQUIRED_AXES, validate_tags

_LOAD_ERRORS: list[tuple[str, list[str]]] = []


def E(
    id: str,
    order: int,
    year_ah: int,
    period: str,
    title_ar: str,
    title_en: str,
    location: str,
    verses: list[str],
    description_ar: str,
    lesson_ar: str,
    pressure_type,
    parties,
    stakes,
    response_category: str,
    principle_class: str,
    polarity,
    response_type: str = "guidance",
) -> dict:
    """Compact event builder. Accepts string or list for multi-valued axes."""
    def _listify(x):
        return x if isinstance(x, list) else [x]

    tags = {
        "pressure_type":     _listify(pressure_type),
        "parties":           _listify(parties),
        "stakes":            _listify(stakes),
        "response_category": response_category,
        "principle_class":   principle_class,
        "polarity":          _listify(polarity),
    }
    errs = validate_tags(tags)
    if errs:
        # Collect for end-of-load report rather than failing on first error
        _LOAD_ERRORS.append((id, errs))

    return {
        "id": id,
        "order": order,
        "year_ah": year_ah,
        "period": period,
        "title_ar": title_ar,
        "title_en": title_en,
        "location": location,
        "verses": verses,
        "description_ar": description_ar,
        "lesson_ar": lesson_ar,
        "response_type": response_type,
        "tags": tags,
    }


# Concatenate all sub-module event lists (split by period for reviewability)
from training.pipeline.sira_db.meccan import MECCAN_EVENTS                   # noqa: E402
from training.pipeline.sira_db.medinan_early import MEDINAN_EARLY_EVENTS     # noqa: E402
from training.pipeline.sira_db.medinan_middle import MEDINAN_MIDDLE_EVENTS   # noqa: E402
from training.pipeline.sira_db.medinan_late import MEDINAN_LATE_EVENTS       # noqa: E402
from training.pipeline.sira_db.asbab import ASBAB_EVENTS                     # noqa: E402

EVENTS: list[dict] = (
    MECCAN_EVENTS
    + MEDINAN_EARLY_EVENTS
    + MEDINAN_MIDDLE_EVENTS
    + MEDINAN_LATE_EVENTS
    + ASBAB_EVENTS
)


def count_by_period() -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in EVENTS:
        counts[e["period"]] = counts.get(e["period"], 0) + 1
    return counts


def validate_all() -> list[str]:
    """Return list of validation errors across all events."""
    errs: list[str] = []
    seen_ids: set[str] = set()
    for e in EVENTS:
        if e["id"] in seen_ids:
            errs.append(f"duplicate event id: {e['id']}")
        seen_ids.add(e["id"])
        for axis in REQUIRED_AXES:
            if axis not in e["tags"]:
                errs.append(f"{e['id']}: missing required axis {axis}")
    return errs
