"""Tests for the Audit Logger (Sprint 6E)."""

import json
import os
import tempfile  # pylint: disable=wrong-import-order

from al_furqan.engine.security.audit import AuditLogger


class TestAuditLogger:
    """Test suite for AuditLogger."""

    def setup_method(self):
        """Execute setup_method."""
        self.tmpdir = tempfile.mkdtemp()  # pylint: disable=attribute-defined-outside-init
        self.logger = AuditLogger(log_dir=self.tmpdir)  # pylint: disable=attribute-defined-outside-init

    def _log_sample(self, eval_id="eval_001", **overrides):
        defaults = dict(  # pylint: disable=use-dict-literal
            evaluation_id=eval_id,
            question_hash="abc123hash",
            axiom_hash="axiom_hash_val",
            gate_hash="gate_hash_val",
            gate_scores=[
                {"name": "Source Integrity", "score": 85, "result": "Survive"},
                {"name": "Structural Consistency", "score": 80, "result": "Survive"},
                {"name": "Mediation Zeroing", "score": 75, "result": "Survive"},
                {"name": "Origin Aware", "score": 90, "result": "Survive"},
            ],
            z3_result=True,
            model_used="test-model",
            processing_time_ms=150.5,
            prompt_injection_detected=False,
        )
        defaults.update(overrides)
        return self.logger.log_evaluation(**defaults)

    def test_log_creation(self):
        """Log file should be created on disk."""
        self._log_sample("eval_test_001")
        path = os.path.join(self.tmpdir, "eval_test_001.json")
        assert os.path.exists(path)

    def test_log_content_correct(self):
        """Logged content should match input."""
        entry = self._log_sample("eval_test_002")
        assert entry["evaluation_id"] == "eval_test_002"
        assert entry["question_hash"] == "abc123hash"
        assert entry["integrity_verified"] is True
        assert entry["prompt_injection_detected"] is False
        assert "timestamp" in entry

        # Verify file content matches
        path = os.path.join(self.tmpdir, "eval_test_002.json")
        with open(path) as f:  # pylint: disable=unspecified-encoding
            saved = json.load(f)
        assert saved["evaluation_id"] == "eval_test_002"

    def test_stats_computation(self):
        """get_stats should compute correct aggregates."""
        self._log_sample("eval_s1", processing_time_ms=100.0)
        self._log_sample("eval_s2", processing_time_ms=200.0)
        self._log_sample("eval_s3", processing_time_ms=300.0, prompt_injection_detected=True)

        stats = self.logger.get_stats()
        assert stats["total_evaluations"] == 3
        assert stats["prompt_injections_detected"] == 1
        assert stats["average_processing_ms"] == 200.0

    def test_stats_empty_dir(self):
        """Stats on empty log dir should return zeros."""
        empty = tempfile.mkdtemp()
        logger = AuditLogger(log_dir=empty)
        stats = logger.get_stats()
        assert stats["total_evaluations"] == 0

    def test_anomaly_detection_hash_change(self):
        """Changing axiom hash across evaluations should be flagged."""
        self._log_sample("eval_a1", axiom_hash="hash_A")
        self._log_sample("eval_a2", axiom_hash="hash_A")
        self._log_sample("eval_a3", axiom_hash="hash_B")  # Changed!

        anomalies = self.logger.detect_anomaly()
        assert any("Axiom hash changed" in a for a in anomalies)

    def test_no_anomaly_when_consistent(self):
        """Consistent evaluations should produce no anomalies."""
        for i in range(5):
            self._log_sample(
                f"eval_c{i}",
                axiom_hash="same_hash",
                gate_scores=[
                    {"name": "G1", "score": 70 + i, "result": "Survive"},
                ],
            )
        anomalies = self.logger.detect_anomaly()
        # No hash change anomaly
        assert not any("Axiom hash changed" in a for a in anomalies)

    def test_hash_question_static_method(self):
        """hash_question should return deterministic SHA-256."""
        h1 = AuditLogger.hash_question("test question")
        h2 = AuditLogger.hash_question("test question")
        assert h1 == h2
        assert len(h1) == 64

    def test_hash_question_different_inputs(self):
        """Different questions should produce different hashes."""
        h1 = AuditLogger.hash_question("question A")
        h2 = AuditLogger.hash_question("question B")
        assert h1 != h2

    def test_injection_detection_anomaly(self):
        """High injection rate should be flagged."""
        for i in range(6):
            self._log_sample(
                f"eval_inj{i}",
                axiom_hash="same",
                prompt_injection_detected=True,
            )
        anomalies = self.logger.detect_anomaly()
        assert any("injection rate" in a.lower() for a in anomalies)
