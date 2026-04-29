"""
KB Tools — أدوات البحث في الـ Tafsir KB.

These tools are exposed to the LLM via function calling.
The LLM decides when and how to use them during reasoning.
"""

import sqlite3
from dataclasses import dataclass


@dataclass
class KBEntry:  # pylint: disable=too-many-instance-attributes
    """A single entry from the Tafsir KB."""

    id: str
    source_node: str  # الآية المركزية (e.g., "6:5")
    target_node: str  # الآية/المفهوم المرتبط
    edge_type: str  # LINKED_VERSE / LINKED_HADITH / HAS_TAFSIR
    provenance: str  # كلام الشيخ المباشر
    reasoning: str  # شرح العلاقة
    confidence: float  # 0.0-1.0
    timestamp_start: float = 0.0
    timestamp_end: float = 0.0

    def format_for_llm(self) -> str:
        """Format entry for LLM consumption."""
        return (
            f"[{self.edge_type}] {self.source_node} → {self.target_node}\n"
            f"الثقة: {self.confidence}\n"
            f"التفسير: {self.reasoning}\n"
        )


class TafsirKBTools:
    """
    Tools for searching the Tafsir Knowledge Base.

    Exposed to the LLM as callable functions during reasoning.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _rows_to_entries(self, rows: list, columns: list[str]) -> list[KBEntry]:
        """Convert DB rows to KBEntry objects."""
        entries = []
        col_map = {c: i for i, c in enumerate(columns)}
        for row in rows:
            entries.append(
                KBEntry(
                    id=row[col_map.get("id", 0)],
                    source_node=row[col_map.get("source_node", 1)],
                    target_node=row[col_map.get("target_node", 2)],
                    edge_type=row[col_map.get("edge_type", 3)],
                    provenance=row[col_map.get("provenance", 4)] or "",
                    reasoning=row[col_map.get("llm_reasoning", 5)] or "",
                    confidence=row[col_map.get("llm_confidence", 6)] or 0.0,
                    timestamp_start=row[col_map.get("timestamp_start", 7)] or 0.0,
                    timestamp_end=row[col_map.get("timestamp_end", 8)] or 0.0,
                )
            )
        return entries

    def search_by_verse(self, verse_ref: str) -> list[KBEntry]:
        """
        Search KB by verse reference.

        Returns all edges where the verse is source or target.
        Tool name for LLM: search_kb_by_verse

        Args:
            verse_ref: Verse reference (e.g., "6:5")

        Returns:
            List of KB entries related to this verse.
        """
        db = self._connect()
        cur = db.cursor()
        cur.execute(
            """
            SELECT id, source_node, target_node, edge_type, provenance,
                   llm_reasoning, llm_confidence, timestamp_start, timestamp_end
            FROM proposed_edges
            WHERE source_node = ? OR target_node = ? OR target_node LIKE ?
            ORDER BY llm_confidence DESC
        """,
            (verse_ref, verse_ref, f"{verse_ref}%"),
        )
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall()
        db.close()
        return self._rows_to_entries(rows, columns)

    def search_by_topic(self, topic: str) -> list[KBEntry]:
        """
        Search KB by topic using text matching.

        Tool name for LLM: search_kb_by_topic

        Args:
            topic: Topic string in Arabic (e.g., "السنة الإلهية")

        Returns:
            List of KB entries matching the topic.
        """
        db = self._connect()
        cur = db.cursor()
        # Search in reasoning, provenance, and target_node
        pattern = f"%{topic}%"
        cur.execute(
            """
            SELECT id, source_node, target_node, edge_type, provenance,
                   llm_reasoning, llm_confidence, timestamp_start, timestamp_end
            FROM proposed_edges
            WHERE llm_reasoning LIKE ?
               OR provenance LIKE ?
               OR target_node LIKE ?
            ORDER BY llm_confidence DESC
        """,
            (pattern, pattern, pattern),
        )
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall()
        db.close()
        return self._rows_to_entries(rows, columns)

    def search_by_relation(self, verse_ref: str, relation_type: str) -> list[KBEntry]:
        """
        Search KB by verse + specific relation type.

        Tool name for LLM: search_kb_by_relation

        Args:
            verse_ref: Verse reference (e.g., "6:5")
            relation_type: Edge type (LINKED_VERSE / LINKED_HADITH / HAS_TAFSIR)

        Returns:
            List of KB entries matching verse + relation type.
        """
        db = self._connect()
        cur = db.cursor()
        cur.execute(
            """
            SELECT id, source_node, target_node, edge_type, provenance,
                   llm_reasoning, llm_confidence, timestamp_start, timestamp_end
            FROM proposed_edges
            WHERE (source_node = ? OR target_node = ?)
              AND edge_type = ?
            ORDER BY llm_confidence DESC
        """,
            (verse_ref, verse_ref, relation_type),
        )
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall()
        db.close()
        return self._rows_to_entries(rows, columns)

    def get_verse_context(self, verse_ref: str, verse_range: int = 3) -> dict:  # pylint: disable=too-many-locals
        """
        Get surrounding verses and their KB entries.

        Tool name for LLM: get_verse_context

        Args:
            verse_ref: Central verse (e.g., "6:5")
            verse_range: How many verses before/after to include.

        Returns:
            Dict with verse texts and KB entries for the range.
        """
        parts = verse_ref.split(":")
        if len(parts) != 2:
            return {"error": f"Invalid verse ref: {verse_ref}"}

        surah = int(parts[0])
        ayah = int(parts[1])

        start = max(1, ayah - verse_range)
        end = ayah + verse_range

        # Get all KB entries in this range
        db = self._connect()
        cur = db.cursor()

        all_entries = []
        for a in range(start, end + 1):
            ref = f"{surah}:{a}"
            cur.execute(
                """
                SELECT id, source_node, target_node, edge_type, provenance,
                       llm_reasoning, llm_confidence, timestamp_start, timestamp_end
                FROM proposed_edges
                WHERE source_node = ?
                ORDER BY llm_confidence DESC
            """,
                (ref,),
            )
            columns = [d[0] for d in cur.description]
            rows = cur.fetchall()
            entries = self._rows_to_entries(rows, columns)
            if entries:
                all_entries.extend(entries)

        db.close()

        return {
            "center": verse_ref,
            "range": f"{surah}:{start}-{surah}:{end}",
            "entries": all_entries,
            "entry_count": len(all_entries),
        }

    def get_all_central_verses(self) -> list[str]:
        """Get all unique central (source) verses in the KB."""
        db = self._connect()
        cur = db.cursor()
        cur.execute("""
            SELECT DISTINCT source_node FROM proposed_edges
            ORDER BY source_node
        """)
        verses = [r[0] for r in cur.fetchall()]
        db.close()
        return verses

    def get_stats(self) -> dict:
        """Get KB statistics."""
        db = self._connect()
        cur = db.cursor()
        cur.execute("SELECT count(*) FROM proposed_edges")
        total = cur.fetchone()[0]
        cur.execute("SELECT DISTINCT source_node FROM proposed_edges")
        sources = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT edge_type, count(*) FROM proposed_edges GROUP BY edge_type")
        by_type = {r[0]: r[1] for r in cur.fetchall()}
        db.close()
        return {
            "total_entries": total,
            "central_verses": sources,
            "by_type": by_type,
        }

    # --- Tool Definitions for LLM Function Calling ---

    @staticmethod
    def get_tool_definitions() -> list[dict]:
        """
        Return tool definitions in OpenAI function-calling format.
        These get passed to the LLM so it can call them.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_kb_by_verse",
                    "description": "ابحث في قاعدة المعرفة التفسيرية عن آية محددة. يرجع كل العلاقات المرتبطة بها (آيات مرتبطة، أحاديث، تفسير عام).",  # pylint: disable=line-too-long
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "verse_ref": {
                                "type": "string",
                                "description": "رقم السورة:رقم الآية (مثال: '6:5' للآية 5 من سورة الأنعام)",  # pylint: disable=line-too-long
                            }
                        },
                        "required": ["verse_ref"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_kb_by_topic",
                    "description": "ابحث في قاعدة المعرفة التفسيرية عن موضوع معين (مثل: 'السنة الإلهية'، 'محاجة المشركين'، 'يوم بدر').",  # pylint: disable=line-too-long
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "الموضوع المراد البحث عنه بالعربية",
                            }
                        },
                        "required": ["topic"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_kb_by_relation",
                    "description": "ابحث عن نوع علاقة محدد لآية معينة (LINKED_VERSE = آيات مرتبطة، LINKED_HADITH = أحاديث، HAS_TAFSIR = تفسير عام).",  # pylint: disable=line-too-long
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "verse_ref": {
                                "type": "string",
                                "description": "رقم السورة:رقم الآية",
                            },
                            "relation_type": {
                                "type": "string",
                                "enum": ["LINKED_VERSE", "LINKED_HADITH", "HAS_TAFSIR"],
                                "description": "نوع العلاقة",
                            },
                        },
                        "required": ["verse_ref", "relation_type"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_verse_context",
                    "description": "اجلب سياق الآية — الآيات المحيطة بها وما يتوفر من تفسير لها في قاعدة المعرفة.",  # pylint: disable=line-too-long
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "verse_ref": {
                                "type": "string",
                                "description": "رقم السورة:رقم الآية",
                            },
                            "verse_range": {
                                "type": "integer",
                                "description": "عدد الآيات قبل وبعد (الافتراضي 3)",
                                "default": 3,
                            },
                        },
                        "required": ["verse_ref"],
                    },
                },
            },
        ]
