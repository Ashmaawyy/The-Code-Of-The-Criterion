"""
Graph Schema — node and edge type definitions for the knowledge graph.

Defines Pydantic models for all node types (Ayah, Hadith, FiqhRule, Scholar,
Topic, Maqsad) and edge types used in the Islamic knowledge graph.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Edge type constants
# ---------------------------------------------------------------------------


class EdgeType(str, Enum):
    """Canonical edge types for the knowledge graph."""

    REFERENCES = "REFERENCES"  # Ayah ↔ Ayah cross-reference
    EXPLAINS = "EXPLAINS"  # Hadith explains Ayah
    SUPPORTS = "SUPPORTS"  # Source supports a ruling
    ESTABLISHES = "ESTABLISHES"  # Source establishes a fiqh rule
    INTERPRETED_BY = "INTERPRETED_BY"  # Node interpreted by a scholar
    NARRATES = "NARRATES"  # Scholar narrates hadith
    BELONGS_TO = "BELONGS_TO"  # Node belongs to a topic
    SERVES = "SERVES"  # Node serves a maqsad
    RELATED_TO = "RELATED_TO"  # General relationship
    DERIVED_FROM = "DERIVED_FROM"  # Rule derived from source


# ---------------------------------------------------------------------------
# Node type constants
# ---------------------------------------------------------------------------


class NodeType(str, Enum):
    """NodeType class."""

    AYAH = "ayah"
    HADITH = "hadith"
    FIQH_RULE = "fiqh_rule"
    SCHOLAR = "scholar"
    TOPIC = "topic"
    MAQSAD = "maqsad"


# ---------------------------------------------------------------------------
# Node models
# ---------------------------------------------------------------------------


class AyahNode(BaseModel):  # pylint: disable=too-few-public-methods
    """A Qur'anic verse node."""

    id: str  # "ayah:2:255"
    surah: int
    ayah: int
    text_ar: str
    text_en: str = ""
    topics: list[str] = Field(default_factory=list)


class HadithNode(BaseModel):  # pylint: disable=too-few-public-methods
    """A Hadith node."""

    id: str  # "hadith:bukhari:1"
    collection: str
    number: int
    text_ar: str
    text_en: str = ""
    grading: str = ""
    narrator: str = ""


class FiqhRuleNode(BaseModel):  # pylint: disable=too-few-public-methods
    """A Fiqh rule / legal maxim node."""

    id: str  # "fiqh:1"
    text_ar: str
    text_en: str = ""
    category: str = ""


class ScholarNode(BaseModel):  # pylint: disable=too-few-public-methods
    """A scholar node."""

    id: str  # "scholar:ibn-taymiyyah"
    name: str


class TopicNode(BaseModel):  # pylint: disable=too-few-public-methods
    """A topic / concept node."""

    id: str  # "topic:riba"
    name_ar: str
    name_en: str = ""


class MaqsadNode(BaseModel):  # pylint: disable=too-few-public-methods
    """One of the Maqasid al-Shariah objectives."""

    id: str  # "maqsad:nafs"
    name_ar: str
    name_en: str
    description: str = ""


# ---------------------------------------------------------------------------
# Edge model
# ---------------------------------------------------------------------------


class ProvenanceType(str, Enum):
    """Accepted provenance types for edge sourcing."""

    TAFSIR = "tafsir"  # كتاب تفسير معتمد (ابن كثير، الطبري، الجلالين)
    SCHOLARLY_LECTURE = (
        "scholarly_lecture"  # درس عالم شرعي موثق (الشيخ أحمد السيد، إلخ)
    )
    FIQH_BOOK = "fiqh_book"  # كتاب فقه معتمد
    HADITH_ISNAD = "hadith_isnad"  # إسناد حديث مرتبط بآية في المتن
    IJMA = "ijma"  # إجماع علماء
    QURAN_INTERNAL = "quran_internal"  # ربط داخلي في القرآن (ناسخ/منسوخ، سبب نزول)
    SCHOLARLY_CONSENSUS = "scholarly_consensus"  # اتفاق علماء معاصرين
    CURATED_VERIFIED = "curated_verified"  # بيانات مراجعة يدوياً من فريق شرعي


class GraphEdge(BaseModel):  # pylint: disable=too-few-public-methods
    """
    A directed edge in the knowledge graph.

    Every edge MUST have provenance — the scholarly source that establishes
    this relationship. Edges without provenance are rejected.

    This is a core design principle: no algorithmic or AI-generated
    relationships are accepted. Only relationships established by:
    1. A verified scholar (e.g., الشيخ أحمد السيد في دروسه)
    2. An authoritative tafsir (e.g., ابن كثير، الطبري، الجلالين)
    3. An authoritative fiqh book
    4. Explicit hadith isnad connection to a verse
    """

    source: str
    target: str
    edge_type: str  # EdgeType value or free string
    weight: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Provenance — مصدر الربط (REQUIRED)
    provenance: str = ""  # المصدر: "tafsir_ibn_kathir" / "sheikh_ahmad_alsayed"
    provenance_type: str = ""  # نوع المصدر: ProvenanceType value
    reference: str = ""  # المرجع التفصيلي: "تفسير ابن كثير ج2 ص340" / "الدرس 15 — سلسلة أصول الفقه"  # pylint: disable=line-too-long
    verified_by: str = ""  # مين راجع الربط ده
    confidence: float = 1.0  # 1.0 = مصدر مباشر, 0.8 = استنباط من مصدر


# ---------------------------------------------------------------------------
# The five Maqasid al-Shariah (pre-defined constants)
# ---------------------------------------------------------------------------

MAQASID_AL_SHARIAH: list[MaqsadNode] = [
    MaqsadNode(
        id="maqsad:deen",
        name_ar="حفظ الدين",
        name_en="Preservation of Religion",
        description="حماية الدين والعقيدة من كل ما يهددها أو يضعفها",
    ),
    MaqsadNode(
        id="maqsad:nafs",
        name_ar="حفظ النفس",
        name_en="Preservation of Life",
        description="حماية النفس البشرية وصون حياتها وكرامتها",
    ),
    MaqsadNode(
        id="maqsad:aql",
        name_ar="حفظ العقل",
        name_en="Preservation of Intellect",
        description="حماية العقل من كل ما يفسده أو يعطله",
    ),
    MaqsadNode(
        id="maqsad:nasl",
        name_ar="حفظ النسل",
        name_en="Preservation of Lineage",
        description="حماية النسل والأسرة والنسب",
    ),
    MaqsadNode(
        id="maqsad:maal",
        name_ar="حفظ المال",
        name_en="Preservation of Wealth",
        description="حماية المال من الضياع والإسراف والتعدي",
    ),
]
