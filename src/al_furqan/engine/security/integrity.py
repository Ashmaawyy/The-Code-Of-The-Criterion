"""
Axiom Integrity Verifier

Computes SHA-256 hashes of all protected axiom components at init time,
then re-verifies before every evaluation to detect runtime tampering.
"""

import hashlib
from dataclasses import dataclass, field


@dataclass
class IntegrityStatus:
    """Result of an integrity verification check."""

    valid: bool
    axiom_hash: str
    gate_hash: str
    scoring_hash: str
    combined_hash: str
    details: list[str] = field(default_factory=list)


class SecurityError(Exception):
    """Raised when axiom integrity is compromised."""

    # pylint: disable=unnecessary-pass


class IntegrityVerifier:
    """Verifies axioms and gates haven't been tampered with at runtime."""

    def __init__(self):
        self._expected = self._compute_hashes()

    def _compute_hashes(self) -> dict:
        """Compute SHA-256 hashes of all protected components."""
        from al_furqan.engine.axioms import (  # pylint: disable=import-outside-toplevel
            AXIOMS,
            GATE_DEFINITIONS,
            SCORING_RULES,
        )

        axiom_hash = hashlib.sha256(AXIOMS.encode()).hexdigest()
        gate_hash = hashlib.sha256(GATE_DEFINITIONS.encode()).hexdigest()
        scoring_hash = hashlib.sha256(SCORING_RULES.encode()).hexdigest()
        combined = hashlib.sha256(
            (axiom_hash + gate_hash + scoring_hash).encode()
        ).hexdigest()

        return {
            "axiom_hash": axiom_hash,
            "gate_hash": gate_hash,
            "scoring_hash": scoring_hash,
            "combined_hash": combined,
        }

    def verify(self) -> IntegrityStatus:
        """Verify all protected components. Call before every evaluation."""
        current = self._compute_hashes()
        issues = []

        for key in ["axiom_hash", "gate_hash", "scoring_hash", "combined_hash"]:
            if current[key] != self._expected[key]:
                issues.append(f"TAMPERING DETECTED: {key} mismatch")

        return IntegrityStatus(
            valid=len(issues) == 0,
            axiom_hash=current["axiom_hash"],
            gate_hash=current["gate_hash"],
            scoring_hash=current["scoring_hash"],
            combined_hash=current["combined_hash"],
            details=issues,
        )

    def verify_or_die(self) -> None:
        """Verify integrity. Raise SecurityError if tampered."""
        status = self.verify()
        if not status.valid:
            raise SecurityError(
                f"CRITICAL: Axiom integrity violation detected!\n"
                f"Details: {status.details}\n"
                f"The engine will not process any evaluations."
            )

    def get_hashes(self) -> dict:
        """Return current expected hashes (for logging/reference)."""
        return dict(self._expected)
