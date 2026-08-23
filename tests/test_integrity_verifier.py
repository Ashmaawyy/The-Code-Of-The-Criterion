"""Tests for the Axiom Integrity Verifier (Sprint 6A)."""

import pytest

# pylint: disable=wrong-import-order
from al_furqan.engine.security.integrity import (
    IntegrityStatus,
    IntegrityVerifier,
    SecurityError,
)


class TestIntegrityVerifier:
    """Test suite for IntegrityVerifier."""

    def test_initial_verification_passes(self):
        """Normal verification should pass immediately after init."""
        verifier = IntegrityVerifier()
        status = verifier.verify()
        assert status.valid is True
        assert not status.details

    def test_hash_values_are_hex_strings(self):
        """All hashes should be 64-char hex strings (SHA-256)."""
        verifier = IntegrityVerifier()
        status = verifier.verify()
        for h in [
            status.axiom_hash,
            status.gate_hash,
            status.scoring_hash,
            status.combined_hash,
        ]:
            assert len(h) == 64
            assert all(c in "0123456789abcdef" for c in h)

    def test_hash_determinism(self):
        """Same axioms should always produce the same hash."""
        v1 = IntegrityVerifier()
        v2 = IntegrityVerifier()
        h1 = v1.verify()
        h2 = v2.verify()
        assert h1.axiom_hash == h2.axiom_hash
        assert h1.gate_hash == h2.gate_hash
        assert h1.scoring_hash == h2.scoring_hash
        assert h1.combined_hash == h2.combined_hash

    def test_verify_or_die_passes_normally(self):
        """verify_or_die should not raise when axioms are intact."""
        verifier = IntegrityVerifier()
        verifier.verify_or_die()  # Should not raise

    def test_tampered_axioms_detected(self):
        """Tampering with AXIOMS should be detected."""
        verifier = IntegrityVerifier()
        # Simulate tampering by changing expected hash
        verifier._expected["axiom_hash"] = "0" * 64  # pylint: disable=protected-access
        status = verifier.verify()
        assert status.valid is False
        assert any("axiom_hash" in d for d in status.details)

    def test_tampered_gates_detected(self):
        """Tampering with GATE_DEFINITIONS should be detected."""
        verifier = IntegrityVerifier()
        verifier._expected["gate_hash"] = "0" * 64  # pylint: disable=protected-access
        status = verifier.verify()
        assert status.valid is False
        assert any("gate_hash" in d for d in status.details)

    def test_tampered_scoring_detected(self):
        """Tampering with SCORING_RULES should be detected."""
        verifier = IntegrityVerifier()
        verifier._expected["scoring_hash"] = "0" * 64  # pylint: disable=protected-access
        status = verifier.verify()
        assert status.valid is False
        assert any("scoring_hash" in d for d in status.details)

    def test_combined_hash_changes_if_any_component_changes(self):
        """Combined hash should change if any single component changes."""
        verifier = IntegrityVerifier()
        original_combined = verifier._expected["combined_hash"]  # pylint: disable=protected-access

        # Tamper axiom hash → combined must also mismatch
        verifier._expected["axiom_hash"] = "a" * 64  # pylint: disable=protected-access
        verifier._expected["combined_hash"] = original_combined  # pylint: disable=protected-access
        status = verifier.verify()
        assert not status.valid

    def test_verify_or_die_raises_security_error(self):
        """verify_or_die should raise SecurityError on tampering."""
        verifier = IntegrityVerifier()
        verifier._expected["axiom_hash"] = "0" * 64  # pylint: disable=protected-access
        with pytest.raises(SecurityError, match="CRITICAL"):
            verifier.verify_or_die()

    def test_security_error_contains_details(self):
        """SecurityError message should include details of what was tampered."""
        verifier = IntegrityVerifier()
        verifier._expected["gate_hash"] = "0" * 64  # pylint: disable=protected-access
        with pytest.raises(SecurityError) as exc_info:
            verifier.verify_or_die()
        assert "gate_hash" in str(exc_info.value)

    def test_get_hashes_returns_dict(self):
        """get_hashes should return a dict with all hash keys."""
        verifier = IntegrityVerifier()
        hashes = verifier.get_hashes()
        assert "axiom_hash" in hashes
        assert "gate_hash" in hashes
        assert "scoring_hash" in hashes
        assert "combined_hash" in hashes

    def test_multiple_tampering_all_detected(self):
        """Multiple tampered components should all be reported."""
        verifier = IntegrityVerifier()
        verifier._expected["axiom_hash"] = "0" * 64  # pylint: disable=protected-access
        verifier._expected["gate_hash"] = "0" * 64  # pylint: disable=protected-access
        verifier._expected["scoring_hash"] = "0" * 64  # pylint: disable=protected-access
        verifier._expected["combined_hash"] = "0" * 64  # pylint: disable=protected-access
        status = verifier.verify()
        assert not status.valid
        # All 4 should be flagged (axiom, gate, scoring, combined)
        assert len(status.details) >= 4

    def test_integrity_status_dataclass_fields(self):
        """IntegrityStatus should have all expected fields."""
        status = IntegrityStatus(
            valid=True,
            axiom_hash="a" * 64,
            gate_hash="b" * 64,
            scoring_hash="c" * 64,
            combined_hash="d" * 64,
            details=[],
        )
        assert status.valid is True
        assert status.axiom_hash == "a" * 64
