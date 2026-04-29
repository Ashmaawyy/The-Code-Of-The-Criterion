"""
SQLite-based local storage for verdicts, patterns, and feedback.

All data stays on the user's device. No network calls.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from typing import Any


class MemoryStore:
    """SQLite-based local storage for verdicts, patterns, and feedback."""

    def __init__(self, db_path: str = "furqan_memory.db"):
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS verdicts (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                domain TEXT DEFAULT 'islamic',
                verdict_json TEXT NOT NULL,
                total_score INTEGER,
                gate_results TEXT,
                final_judgment TEXT,
                tags TEXT DEFAULT '[]',
                created_at REAL NOT NULL,
                accessed_at REAL,
                access_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                domain TEXT DEFAULT 'islamic',
                rule TEXT NOT NULL,
                signals TEXT NOT NULL,
                expected_gates TEXT NOT NULL,
                expected_score_min INTEGER,
                expected_score_max INTEGER,
                template TEXT,
                confidence REAL DEFAULT 0.3,
                source_verdicts TEXT DEFAULT '[]',
                hit_count INTEGER DEFAULT 0,
                last_hit REAL,
                created_at REAL NOT NULL,
                feedback_score REAL DEFAULT 0.0,
                version INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                target_id TEXT NOT NULL,
                target_type TEXT NOT NULL,
                rating TEXT NOT NULL,
                correction TEXT,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS context (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                domain TEXT DEFAULT 'global',
                updated_at REAL NOT NULL
            );
        """)
        self.db.commit()

    # ---- Verdict CRUD ----

    def save_verdict(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        verdict_id: str,
        question: str,
        verdict_data: dict,
        domain: str = "islamic",
        tags: list | None = None,
    ) -> str:
        """Save a verdict to storage. Returns the verdict ID."""
        now = time.time()
        self.db.execute(
            """INSERT OR REPLACE INTO verdicts
               (id, question, domain, verdict_json, total_score,
                gate_results, final_judgment, tags, created_at, accessed_at, access_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                verdict_id,
                question,
                domain,
                json.dumps(verdict_data, ensure_ascii=False),
                verdict_data.get("total_score"),
                json.dumps(verdict_data.get("gate_results", []), ensure_ascii=False),
                verdict_data.get("final_judgment", ""),
                json.dumps(tags or []),
                now,
                now,
                0,
            ),
        )
        self.db.commit()
        return verdict_id

    def get_verdict(self, verdict_id: str) -> dict | None:
        """Retrieve a verdict by ID. Updates access_count and accessed_at."""
        row = self.db.execute(
            "SELECT * FROM verdicts WHERE id = ?", (verdict_id,)
        ).fetchone()
        if not row:
            return None
        # Update access tracking
        self.db.execute(
            "UPDATE verdicts SET access_count = access_count + 1, accessed_at = ? WHERE id = ?",
            (time.time(), verdict_id),
        )
        self.db.commit()
        return self._row_to_verdict(row)

    def get_recent_verdicts(self, limit: int = 10, domain: str | None = None) -> list[dict]:
        """Get the most recent verdicts, optionally filtered by domain."""
        if domain:
            rows = self.db.execute(
                "SELECT * FROM verdicts WHERE domain = ? ORDER BY created_at DESC LIMIT ?",
                (domain, limit),
            ).fetchall()
        else:
            rows = self.db.execute(
                "SELECT * FROM verdicts ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_verdict(r) for r in rows]

    def search_verdicts(self, query: str, limit: int = 5) -> list[dict]:
        """Simple text search over verdict questions (LIKE-based)."""
        pattern = f"%{query}%"
        rows = self.db.execute(
            "SELECT * FROM verdicts WHERE question LIKE ? ORDER BY created_at DESC LIMIT ?",
            (pattern, limit),
        ).fetchall()
        return [self._row_to_verdict(r) for r in rows]

    # ---- Pattern CRUD ----

    def save_pattern(self, pattern: dict) -> str:
        """Save a pattern. Auto-generates ID if not present."""
        pattern_id = pattern.get("id", f"p_{uuid.uuid4().hex[:12]}")
        now = time.time()
        self.db.execute(
            """INSERT OR REPLACE INTO patterns
               (id, category, domain, rule, signals, expected_gates,
                expected_score_min, expected_score_max, template,
                confidence, source_verdicts, hit_count, last_hit,
                created_at, feedback_score, version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pattern_id,
                pattern.get("category", "general"),
                pattern.get("domain", "islamic"),
                pattern.get("rule", ""),
                json.dumps(pattern.get("signals", []), ensure_ascii=False),
                json.dumps(pattern.get("expected_gates", []), ensure_ascii=False),
                pattern.get("expected_score_min"),
                pattern.get("expected_score_max"),
                pattern.get("template"),
                pattern.get("confidence", 0.3),
                json.dumps(pattern.get("source_verdicts", []), ensure_ascii=False),
                pattern.get("hit_count", 0),
                pattern.get("last_hit"),
                pattern.get("created_at", now),
                pattern.get("feedback_score", 0.0),
                pattern.get("version", 1),
            ),
        )
        self.db.commit()
        return pattern_id

    def get_pattern(self, pattern_id: str) -> dict | None:
        """Retrieve a pattern by ID."""
        row = self.db.execute(
            "SELECT * FROM patterns WHERE id = ?", (pattern_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_pattern(row)

    def get_mature_patterns(self, min_confidence: float = 0.8) -> list[dict]:
        """Get patterns that have reached maturity (high confidence)."""
        rows = self.db.execute(
            "SELECT * FROM patterns WHERE confidence >= ? ORDER BY confidence DESC",
            (min_confidence,),
        ).fetchall()
        return [self._row_to_pattern(r) for r in rows]

    # Column names that may be updated via update_pattern().
    # Each maps to a literal SQL fragment so no dynamic column names ever
    # reach the query string.
    _PATTERN_UPDATE_COLUMNS: dict[str, str] = {
        "confidence": "confidence = ?",
        "hit_count": "hit_count = ?",
        "last_hit": "last_hit = ?",
        "feedback_score": "feedback_score = ?",
        "version": "version = ?",
        "rule": "rule = ?",
        "signals": "signals = ?",
        "expected_gates": "expected_gates = ?",
        "template": "template = ?",
        "source_verdicts": "source_verdicts = ?",
    }
    _PATTERN_JSON_FIELDS = frozenset({"signals", "expected_gates", "source_verdicts"})

    def update_pattern(self, pattern_id: str, updates: dict) -> bool:
        """Update specific fields of a pattern."""
        existing = self.get_pattern(pattern_id)
        if not existing:
            return False

        set_parts = []
        values = []
        for key, value in updates.items():
            clause = self._PATTERN_UPDATE_COLUMNS.get(key)
            if clause is None:
                continue
            if key in self._PATTERN_JSON_FIELDS:
                value = json.dumps(value, ensure_ascii=False)
            set_parts.append(clause)
            values.append(value)

        if not set_parts:
            return False

        values.append(pattern_id)
        self.db.execute(
            "UPDATE patterns SET " + ", ".join(set_parts) + " WHERE id = ?",
            values,
        )
        self.db.commit()
        return True

    # ---- Feedback CRUD ----

    def save_feedback(
        self,
        target_id: str,
        target_type: str,
        rating: str,
        correction: str | None = None,
    ) -> str:
        """Save user feedback on a verdict or pattern."""
        feedback_id = f"f_{uuid.uuid4().hex[:12]}"
        now = time.time()
        self.db.execute(
            """INSERT INTO feedback (id, target_id, target_type, rating, correction, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (feedback_id, target_id, target_type, rating, correction, now),
        )
        self.db.commit()
        return feedback_id

    def get_feedback_for(self, target_id: str) -> list[dict]:
        """Get all feedback for a given target."""
        rows = self.db.execute(
            "SELECT * FROM feedback WHERE target_id = ? ORDER BY created_at DESC",
            (target_id,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "target_id": r["target_id"],
                "target_type": r["target_type"],
                "rating": r["rating"],
                "correction": r["correction"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # ---- Context ----

    def set_context(self, key: str, value: Any, domain: str = "global") -> None:
        """Set a context key-value pair."""
        self.db.execute(
            "INSERT OR REPLACE INTO context (key, value, domain, updated_at) VALUES (?, ?, ?, ?)",
            (key, json.dumps(value, ensure_ascii=False), domain, time.time()),
        )
        self.db.commit()

    def get_context(self, key: str) -> Any | None:
        """Get a context value by key."""
        row = self.db.execute("SELECT value FROM context WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        return json.loads(row["value"])

    # ---- Stats ----

    def get_stats(self, domain: str | None = None) -> dict:
        """Return memory usage statistics."""
        if domain:
            verdict_count = self.db.execute(
                "SELECT COUNT(*) FROM verdicts WHERE domain = ?", (domain,)
            ).fetchone()[0]
            pattern_count = self.db.execute(
                "SELECT COUNT(*) FROM patterns WHERE domain = ?", (domain,)
            ).fetchone()[0]
            feedback_count = self.db.execute(
                """SELECT COUNT(*) FROM feedback f
                   JOIN verdicts v ON f.target_id = v.id
                   WHERE v.domain = ?""",
                (domain,),
            ).fetchone()[0]
            mature_count = self.db.execute(
                "SELECT COUNT(*) FROM patterns WHERE domain = ? AND confidence >= 0.8",
                (domain,),
            ).fetchone()[0]
        else:
            verdict_count = self.db.execute("SELECT COUNT(*) FROM verdicts").fetchone()[0]
            pattern_count = self.db.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]
            feedback_count = self.db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
            mature_count = self.db.execute(
                "SELECT COUNT(*) FROM patterns WHERE confidence >= 0.8"
            ).fetchone()[0]

        return {
            "verdicts": verdict_count,
            "patterns": pattern_count,
            "mature_patterns": mature_count,
            "feedback_entries": feedback_count,
            "domain": domain or "all",
        }

    # ---- Cleanup ----

    def close(self) -> None:
        """Close the database connection."""
        self.db.close()

    # ---- Internal helpers ----

    @staticmethod
    def _row_to_verdict(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "question": row["question"],
            "domain": row["domain"],
            "verdict_data": json.loads(row["verdict_json"]),
            "total_score": row["total_score"],
            "gate_results": json.loads(row["gate_results"]) if row["gate_results"] else [],
            "final_judgment": row["final_judgment"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "created_at": row["created_at"],
            "accessed_at": row["accessed_at"],
            "access_count": row["access_count"],
        }

    @staticmethod
    def _row_to_pattern(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "category": row["category"],
            "domain": row["domain"],
            "rule": row["rule"],
            "signals": json.loads(row["signals"]) if row["signals"] else [],
            "expected_gates": json.loads(row["expected_gates"]) if row["expected_gates"] else [],
            "expected_score_min": row["expected_score_min"],
            "expected_score_max": row["expected_score_max"],
            "template": row["template"],
            "confidence": row["confidence"],
            "source_verdicts": json.loads(row["source_verdicts"]) if row["source_verdicts"] else [],
            "hit_count": row["hit_count"],
            "last_hit": row["last_hit"],
            "created_at": row["created_at"],
            "feedback_score": row["feedback_score"],
            "version": row["version"],
        }
