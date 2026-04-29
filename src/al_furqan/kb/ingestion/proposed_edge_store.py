"""
Proposed Edge Store — SQLite storage for KG edges awaiting human review.

All LLM-extracted edges land here with status="pending".
Nothing enters the Knowledge Graph until a human confirms it.
"""

import os
import sqlite3
import time
from typing import List, Optional

from al_furqan.paths import PROPOSED_EDGES_DB

from .models import ProposedEdge


SCHEMA = """
CREATE TABLE IF NOT EXISTS proposed_edges (
    id TEXT PRIMARY KEY,
    lesson_id TEXT NOT NULL,
    source_node TEXT NOT NULL,
    target_node TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    provenance TEXT NOT NULL,
    provenance_type TEXT NOT NULL,
    reference TEXT NOT NULL,
    timestamp_start TEXT NOT NULL,
    timestamp_end TEXT NOT NULL,
    transcript_chunk TEXT NOT NULL,
    llm_reasoning TEXT NOT NULL,
    llm_confidence REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    reviewed_by TEXT NOT NULL DEFAULT '',
    review_notes TEXT NOT NULL DEFAULT '',
    review_timestamp REAL NOT NULL DEFAULT 0.0
);

CREATE INDEX IF NOT EXISTS idx_status ON proposed_edges(status);
CREATE INDEX IF NOT EXISTS idx_lesson ON proposed_edges(lesson_id);
CREATE INDEX IF NOT EXISTS idx_edge_type ON proposed_edges(edge_type);
"""

COLUMNS = [
    "id",
    "lesson_id",
    "source_node",
    "target_node",
    "edge_type",
    "provenance",
    "provenance_type",
    "reference",
    "timestamp_start",
    "timestamp_end",
    "transcript_chunk",
    "llm_reasoning",
    "llm_confidence",
    "status",
    "reviewed_by",
    "review_notes",
    "review_timestamp",
]


class ProposedEdgeStore:
    """SQLite-backed store for proposed KG edges."""

    def __init__(self, db_path: str = str(PROPOSED_EDGES_DB)):
        self.db_path = db_path
        os.makedirs(
            os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True
        )
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)

    def close(self):
        """Close the database connection."""
        self._conn.close()

    def _row_to_edge(self, row: sqlite3.Row) -> ProposedEdge:
        """Convert a database row to a ProposedEdge."""
        return ProposedEdge(**{col: row[col] for col in COLUMNS})

    # ----- Write Operations -----

    def save(self, edge: ProposedEdge) -> None:
        """Save a proposed edge to the store."""
        placeholders = ", ".join(["?"] * len(COLUMNS))
        col_names = ", ".join(COLUMNS)
        values = [getattr(edge, col) for col in COLUMNS]
        self._conn.execute(
            f"INSERT OR REPLACE INTO proposed_edges ({col_names}) VALUES ({placeholders})",
            values,
        )
        self._conn.commit()

    def save_batch(self, edges: List[ProposedEdge]) -> None:
        """Save multiple edges in a single transaction."""
        placeholders = ", ".join(["?"] * len(COLUMNS))
        col_names = ", ".join(COLUMNS)
        rows = [[getattr(e, col) for col in COLUMNS] for e in edges]
        self._conn.executemany(
            f"INSERT OR REPLACE INTO proposed_edges ({col_names}) VALUES ({placeholders})",
            rows,
        )
        self._conn.commit()

    # ----- Read Operations -----

    def get_by_id(self, edge_id: str) -> Optional[ProposedEdge]:
        """Get a single edge by ID."""
        row = self._conn.execute(
            "SELECT * FROM proposed_edges WHERE id = ?", (edge_id,)
        ).fetchone()
        return self._row_to_edge(row) if row else None

    def get_pending(
        self, lesson_id: Optional[str] = None, limit: int = 100
    ) -> List[ProposedEdge]:
        """Get pending edges, optionally filtered by lesson."""
        if lesson_id:
            rows = self._conn.execute(
                "SELECT * FROM proposed_edges WHERE status = 'pending' AND lesson_id = ? LIMIT ?",
                (lesson_id, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM proposed_edges WHERE status = 'pending' LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_edge(r) for r in rows]

    def get_by_status(self, status: str, limit: int = 100) -> List[ProposedEdge]:
        """Get edges by status."""
        rows = self._conn.execute(
            "SELECT * FROM proposed_edges WHERE status = ? LIMIT ?",
            (status, limit),
        ).fetchall()
        return [self._row_to_edge(r) for r in rows]

    def get_all(self, lesson_id: Optional[str] = None) -> List[ProposedEdge]:
        """Get all edges, optionally filtered by lesson."""
        if lesson_id:
            rows = self._conn.execute(
                "SELECT * FROM proposed_edges WHERE lesson_id = ?", (lesson_id,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM proposed_edges").fetchall()
        return [self._row_to_edge(r) for r in rows]

    # ----- Review Operations -----

    def confirm(self, edge_id: str, reviewed_by: str, notes: str = "") -> bool:
        """Confirm a pending edge."""
        return self._update_status(edge_id, "confirmed", reviewed_by, notes)

    def reject(self, edge_id: str, reviewed_by: str, notes: str = "") -> bool:
        """Reject a pending edge."""
        return self._update_status(edge_id, "rejected", reviewed_by, notes)

    def edit_and_confirm(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        edge_id: str,
        reviewed_by: str,
        notes: str = "",
        source_node: Optional[str] = None,
        target_node: Optional[str] = None,
        edge_type: Optional[str] = None,
    ) -> bool:
        """Edit fields and confirm an edge."""
        edge = self.get_by_id(edge_id)
        if not edge:
            return False

        updates = {
            "status": "edited",
            "reviewed_by": reviewed_by,
            "review_notes": notes,
            "review_timestamp": time.time(),
        }
        if source_node is not None:
            updates["source_node"] = source_node
        if target_node is not None:
            updates["target_node"] = target_node
        if edge_type is not None:
            updates["edge_type"] = edge_type

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [edge_id]
        cursor = self._conn.execute(
            f"UPDATE proposed_edges SET {set_clause} WHERE id = ?",
            values,
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def _update_status(
        self, edge_id: str, status: str, reviewed_by: str, notes: str
    ) -> bool:
        """Update edge status with review metadata."""
        cursor = self._conn.execute(
            """UPDATE proposed_edges
               SET status = ?, reviewed_by = ?, review_notes = ?, review_timestamp = ?
               WHERE id = ?""",
            (status, reviewed_by, notes, time.time(), edge_id),
        )
        self._conn.commit()
        return cursor.rowcount > 0

    # ----- Analytics -----

    def get_stats(self) -> dict:
        """Get summary statistics."""
        rows = self._conn.execute(
            "SELECT status, COUNT(*) as cnt FROM proposed_edges GROUP BY status"
        ).fetchall()
        stats = {row["status"]: row["cnt"] for row in rows}
        stats["total"] = sum(stats.values())

        # Average confidence
        row = self._conn.execute(
            "SELECT AVG(llm_confidence) as avg_conf FROM proposed_edges"
        ).fetchone()
        stats["avg_confidence"] = round(row["avg_conf"], 3) if row["avg_conf"] else 0.0

        return stats

    def get_rejection_patterns(self) -> List[dict]:
        """Analyze rejection patterns to improve future extractions."""
        rows = self._conn.execute(
            """SELECT edge_type, review_notes, COUNT(*) as cnt
               FROM proposed_edges
               WHERE status = 'rejected'
               GROUP BY edge_type, review_notes
               ORDER BY cnt DESC
               LIMIT 20"""
        ).fetchall()
        return [
            {"edge_type": r["edge_type"], "notes": r["review_notes"], "count": r["cnt"]}
            for r in rows
        ]  # pylint: disable=line-too-long
