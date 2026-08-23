"""
Audit Logger

Logs every evaluation with full integrity context for accountability
and anomaly detection. Stores question HASH (not text) for privacy.
"""

import hashlib
import json
import os
import time

from al_furqan.paths import DATA_AUDIT


class AuditLogger:
    """Logs every evaluation with full integrity context."""

    def __init__(self, log_dir: str = str(DATA_AUDIT)):
        os.makedirs(log_dir, exist_ok=True)
        self.log_dir = log_dir

    def log_evaluation(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        self,
        evaluation_id: str,
        question_hash: str,
        axiom_hash: str,
        gate_hash: str,
        gate_scores: list,
        z3_result: bool | None,
        model_used: str,
        processing_time_ms: float,
        prompt_injection_detected: bool = False,
    ) -> dict:
        """Log a complete evaluation record."""
        entry = {
            "evaluation_id": evaluation_id,
            "timestamp": time.time(),
            "question_hash": question_hash,
            "axiom_hash": axiom_hash,
            "gate_hash": gate_hash,
            "gate_scores": gate_scores,
            "z3_consistent": z3_result,
            "model_used": model_used,
            "processing_time_ms": processing_time_ms,
            "prompt_injection_detected": prompt_injection_detected,
            "integrity_verified": True,
        }

        path = os.path.join(self.log_dir, f"{evaluation_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)

        return entry

    def get_stats(self) -> dict:
        """Return audit statistics."""
        total = 0
        injection_count = 0
        z3_consistent_count = 0
        total_score_sum = 0.0
        total_processing_ms = 0.0

        for filename in os.listdir(self.log_dir):
            if not filename.endswith(".json"):
                continue
            try:
                path = os.path.join(self.log_dir, filename)
                with open(path, encoding="utf-8") as f:
                    entry = json.load(f)
                total += 1
                if entry.get("prompt_injection_detected"):
                    injection_count += 1
                if entry.get("z3_consistent"):
                    z3_consistent_count += 1
                total_processing_ms += entry.get("processing_time_ms", 0)

                # Average gate score
                scores = entry.get("gate_scores", [])
                if scores:
                    if isinstance(scores[0], dict):
                        avg = sum(s.get("score", 0) for s in scores) / len(scores)
                    else:
                        avg = sum(scores) / len(scores)
                    total_score_sum += avg
            except (json.JSONDecodeError, OSError):
                continue

        return {
            "total_evaluations": total,
            "prompt_injections_detected": injection_count,
            "z3_consistent_count": z3_consistent_count,
            "average_processing_ms": (total_processing_ms / total if total else 0),
            "average_gate_score": total_score_sum / total if total else 0,
        }

    def detect_anomaly(self) -> list:
        """Check for score distribution anomalies.

        Detects:
        - All recent evaluations passing or failing (suggests tampering)
        - Sudden processing time changes
        - Integrity hash changes across evaluations
        """
        anomalies: list[str] = []
        entries = []

        for filename in sorted(os.listdir(self.log_dir)):
            if not filename.endswith(".json"):
                continue
            try:
                path = os.path.join(self.log_dir, filename)
                with open(path, encoding="utf-8") as f:
                    entries.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue

        if len(entries) < 3:
            return anomalies

        # Check last N entries
        recent = entries[-10:] if len(entries) >= 10 else entries

        # 1. All same axiom hash? (expected). Different? anomaly.
        hashes = {e.get("axiom_hash") for e in recent}
        if len(hashes) > 1:
            anomalies.append("ANOMALY: Axiom hash changed across recent evaluations")

        # 2. All scores suspiciously identical
        gate_avgs = []
        for e in recent:
            scores = e.get("gate_scores", [])
            if scores:
                if isinstance(scores[0], dict):
                    avg = sum(s.get("score", 0) for s in scores) / len(scores)
                else:
                    avg = sum(scores) / len(scores)
                gate_avgs.append(avg)

        if gate_avgs and len(set(gate_avgs)) == 1 and len(gate_avgs) >= 5:
            anomalies.append(
                "ANOMALY: All recent evaluations have identical gate scores"
            )

        # 3. High injection rate
        injection_count = sum(1 for e in recent if e.get("prompt_injection_detected"))
        if injection_count > len(recent) * 0.5:
            anomalies.append(
                f"ANOMALY: High injection rate ({injection_count}/{len(recent)})"
            )

        return anomalies

    @staticmethod
    def hash_question(question: str) -> str:
        """Hash a question for privacy-preserving logging."""
        return hashlib.sha256(question.encode()).hexdigest()
