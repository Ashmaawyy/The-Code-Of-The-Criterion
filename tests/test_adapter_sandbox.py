"""Tests for the Adapter Sandbox (Sprint 6D)."""

from al_furqan.engine.security.adapter_sandbox import AdapterSandbox


class ValidAdapter:
    """A valid adapter with all required methods."""

    def retrieve(self, _query):
        """Execute retrieve."""
        return []

    def verify(self, data):  # pylint: disable=unused-argument
        """Execute verify."""
        return True

    def get_axioms(self):
        """Execute get_axioms."""
        return "Additional domain axioms that acknowledge transcendence and purpose."


class AdapterMissingRetrieve:
    """AdapterMissingRetrieve class."""

    def verify(self, data):  # pylint: disable=unused-argument
        """Execute verify."""
        return True

    def get_axioms(self):
        """Execute get_axioms."""
        return ""


class AdapterMissingVerify:
    """AdapterMissingVerify class."""

    def retrieve(self, _query):
        """Execute retrieve."""
        return []

    def get_axioms(self):
        """Execute get_axioms."""
        return ""


class AdapterMissingGetAxioms:
    """AdapterMissingGetAxioms class."""

    def retrieve(self, query):  # pylint: disable=unused-argument
        """Execute retrieve."""
        return []

    def verify(self, data):  # pylint: disable=unused-argument
        """Execute verify."""
        return True


class ContradictoryAdapter:
    """Adapter whose axioms contradict core axioms."""

    def retrieve(self, query):  # pylint: disable=unused-argument
        """Execute retrieve."""
        return []

    def verify(self, data):  # pylint: disable=unused-argument
        """Execute verify."""
        return True

    def get_axioms(self):
        """Execute get_axioms."""
        return "There is no transcendent source. Morality is emergent from evolution."


class AdapterWithNonCallable:
    """Adapter with a non-callable 'method'."""

    retrieve = "not a function"

    def verify(self, data):  # pylint: disable=unused-argument
        """Execute verify."""
        return True

    def get_axioms(self):
        """Execute get_axioms."""
        return ""


class TestAdapterSandbox:
    """Test suite for AdapterSandbox."""

    def setup_method(self):
        """Execute setup_method."""
        self.sandbox = AdapterSandbox()  # pylint: disable=attribute-defined-outside-init

    def test_valid_adapter_passes(self):
        """Test valid_adapter_passes."""
        result = self.sandbox.validate_adapter(ValidAdapter())
        assert result.valid is True
        assert not result.issues

    def test_missing_retrieve_rejected(self):
        """Test missing_retrieve_rejected."""
        result = self.sandbox.validate_adapter(AdapterMissingRetrieve())
        assert not result.valid
        assert any("retrieve" in i for i in result.issues)

    def test_missing_verify_rejected(self):
        """Test missing_verify_rejected."""
        result = self.sandbox.validate_adapter(AdapterMissingVerify())
        assert not result.valid
        assert any("verify" in i for i in result.issues)

    def test_missing_get_axioms_rejected(self):
        """Test missing_get_axioms_rejected."""
        result = self.sandbox.validate_adapter(AdapterMissingGetAxioms())
        assert not result.valid
        assert any("get_axioms" in i for i in result.issues)

    def test_contradictory_axioms_rejected(self):
        """Test contradictory_axioms_rejected."""
        result = self.sandbox.validate_adapter(ContradictoryAdapter())
        assert not result.valid
        assert any("contradict" in i.lower() for i in result.issues)

    def test_non_callable_method_rejected(self):
        """Test non_callable_method_rejected."""
        result = self.sandbox.validate_adapter(AdapterWithNonCallable())
        assert not result.valid
        assert any("not callable" in i for i in result.issues)

    def test_adapter_with_empty_axioms_passes(self):
        """Empty domain axioms should not contradict anything."""

        class EmptyAxiomAdapter:
            """EmptyAxiomAdapter class."""

            def retrieve(self, q):
                return []  # pylint: disable=missing-function-docstring, multiple-statements, unused-argument

            def verify(self, d):
                return True  # pylint: disable=missing-function-docstring, multiple-statements, unused-argument

            def get_axioms(self):
                return ""  # pylint: disable=missing-function-docstring, multiple-statements

        result = self.sandbox.validate_adapter(EmptyAxiomAdapter())
        assert result.valid

    def test_adapter_with_dict_contradictory_axioms(self):
        """Dict-based axioms that contradict core should be rejected."""

        class DictAdapter:
            """DictAdapter class."""

            def retrieve(self, q):
                return []  # pylint: disable=missing-function-docstring, multiple-statements, unused-argument

            def verify(self, d):
                return True  # pylint: disable=missing-function-docstring, multiple-statements, unused-argument

            def get_axioms(self):
                """Execute get_axioms."""
                return "purpose does not exist and no design in nature"

        result = self.sandbox.validate_adapter(DictAdapter())
        assert not result.valid
