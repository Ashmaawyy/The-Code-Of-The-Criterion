"""Tests for the PredicateExtractor."""

from al_furqan.engine.symbolic.predicate_extractor import PredicateExtractor


class TestPredicateExtractor:
    """Test predicate extraction from chain results."""

    def setup_method(self):
        """Execute setup_method."""
        self.extractor = PredicateExtractor()  # pylint: disable=attribute-defined-outside-init

    def test_empty_dict_returns_empty(self):
        """Empty chain results should produce no predicates."""
        result = self.extractor.extract({})
        assert not result

    def test_none_returns_empty(self):
        """None/falsy input should produce no predicates."""
        result = self.extractor.extract(None)
        assert not result

    def test_divine_source_extraction(self):
        """source_type='divine' should produce HasVerifiedSource predicate."""
        results = {"source_type": "divine"}
        predicates = self.extractor.extract(results)
        assert len(predicates) == 1
        assert "HasVerifiedSource" in str(predicates[0])

    def test_verifiable_source_extraction(self):
        """is_verifiable=True should produce HasVerifiedSource predicate."""
        results = {"is_verifiable": True}
        predicates = self.extractor.extract(results)
        assert len(predicates) == 1
        assert "HasVerifiedSource" in str(predicates[0])

    def test_unverifiable_source_extraction(self):
        """is_verifiable=False should produce Not(HasVerifiedSource)."""
        results = {"is_verifiable": False}
        predicates = self.extractor.extract(results)
        assert len(predicates) == 1
        assert "Not" in str(predicates[0]) or "¬" in str(predicates[0])

    def test_no_contradictions_means_consistent(self):
        """has_contradictions=False → IsInternallyConsistent (inverted logic)."""
        results = {"has_contradictions": False}
        predicates = self.extractor.extract(results)
        assert len(predicates) == 1
        assert "IsInternallyConsistent" in str(predicates[0])
        # Should be positive (consistent), not negated
        assert "Not" not in str(predicates[0])

    def test_has_contradictions_means_inconsistent(self):
        """has_contradictions=True → Not(IsInternallyConsistent)."""
        results = {"has_contradictions": True}
        predicates = self.extractor.extract(results)
        assert len(predicates) == 1
        assert "Not" in str(predicates[0])

    def test_full_chain_results(self):
        """Complete chain results should produce multiple predicates."""
        results = {
            "source_type": "divine",
            "is_verifiable": True,
            "has_contradictions": False,
            "relies_on_human_preference": False,
            "acknowledges_transcendence": True,
        }
        predicates = self.extractor.extract(results)
        # source_type + has_contradictions + relies_on + acknowledges = 4
        # (is_verifiable is overridden by source_type=divine)
        assert len(predicates) >= 4

    def test_custom_entity_name(self):
        """Custom entity name should appear in predicates."""
        results = {"acknowledges_transcendence": True}
        predicates = self.extractor.extract(results, entity_name="islam")
        assert len(predicates) == 1
        assert "islam" in str(predicates[0])

    def test_framework_predicates(self):
        """Framework-level keys should produce framework predicates."""
        results = {
            "is_contingent": True,
            "has_moral_debts": True,
            "human_justice_sufficient": False,
        }
        predicates = self.extractor.extract(results)
        assert len(predicates) == 3

    def test_non_boolean_values_ignored(self):
        """Non-boolean values for mapped keys should be skipped."""
        results = {
            "has_contradictions": "maybe",  # not bool
            "acknowledges_transcendence": 1,  # not bool
        }
        predicates = self.extractor.extract(results)
        assert len(predicates) == 0

    def test_unknown_keys_ignored(self):
        """Keys not in the mapping should be silently ignored."""
        results = {
            "unknown_key": True,
            "random_data": "hello",
            "acknowledges_transcendence": True,
        }
        predicates = self.extractor.extract(results)
        assert len(predicates) == 1
