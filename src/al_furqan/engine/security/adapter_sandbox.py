"""
Adapter Sandbox

Enforces security boundaries for domain adapters. Validates that
adapters implement required interfaces and that their domain axioms
don't contradict core Al-Furqan axioms.
"""

from al_furqan.engine.security.output_validator import ValidationResult


class AdapterSandbox:  # pylint: disable=too-few-public-methods
    """Enforces adapter security boundaries."""

    REQUIRED_METHODS = ["retrieve", "verify", "get_axioms"]

    def validate_adapter(self, adapter) -> ValidationResult:
        """Validate an adapter before registration.

        Checks:
        1. Required methods are present and callable
        2. Domain axioms don't contradict core axioms
        """
        issues: list[str] = []

        # 1. Must have required methods
        for method_name in self.REQUIRED_METHODS:
            if not hasattr(adapter, method_name):
                issues.append(f"Missing required method: {method_name}")
            elif not callable(getattr(adapter, method_name)):
                issues.append(f"Method {method_name} is not callable")

        # If missing critical methods, can't proceed to axiom check
        if not hasattr(adapter, "get_axioms") or not callable(
            getattr(adapter, "get_axioms", None)
        ):
            return ValidationResult(valid=False, issues=issues)

        # 2. Domain axioms must not contradict core
        try:
            domain_axioms = adapter.get_axioms()
            if domain_axioms and self._contradicts_core(domain_axioms):
                issues.append("Domain axioms contradict core axioms — REJECTED")
        except Exception as e:  # pylint: disable=broad-exception-caught
            issues.append(f"Error checking domain axioms: {e}")

        return ValidationResult(valid=len(issues) == 0, issues=issues)

    def _contradicts_core(self, domain_axioms) -> bool:
        """Check if domain axioms contradict core axioms.

        Uses Z3 symbolic verifier when available, falls back to
        keyword-based heuristic check.
        """
        try:
            from al_furqan.engine.symbolic.verifier import (
                SymbolicVerifier,  # pylint: disable=import-outside-toplevel
            )

            verifier = SymbolicVerifier(timeout_ms=5000)

            # Check domain axioms for explicit contradictions
            predicates = self._extract_contradiction_predicates(domain_axioms)
            if predicates:
                result = verifier.verify_predicates(predicates)  # pylint: disable=no-member
                if result.consistent is False:
                    return True
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        # Heuristic fallback: check for explicit negations of core concepts
        return self._heuristic_contradiction_check(domain_axioms)

    def _extract_contradiction_predicates(self, domain_axioms) -> dict:
        """Extract predicates from domain axioms for Z3 verification."""
        if isinstance(domain_axioms, dict):
            return domain_axioms
        if isinstance(domain_axioms, str):
            predicates = {}
            lower = domain_axioms.lower()
            # Check for explicit denials of core axioms
            if "no transcendent" in lower or "deny transcendence" in lower:
                predicates["acknowledges_transcendence"] = False
            if "no purpose" in lower or "purposeless" in lower:
                predicates["has_purpose"] = False
            if "no design" in lower or "undesigned" in lower:
                predicates["exists"] = False
            return predicates
        return {}

    def _heuristic_contradiction_check(self, domain_axioms) -> bool:
        """Simple keyword check for contradictions with core axioms."""
        if isinstance(domain_axioms, str):
            text = domain_axioms.lower()
        elif isinstance(domain_axioms, dict):
            text = str(domain_axioms).lower()
        else:
            return False

        # Core axiom negations
        contradiction_phrases = [
            "there is no transcendent",
            "transcendence is false",
            "purpose does not exist",
            "no design in nature",
            "morality is emergent",
            "no final court",
            "justice ends at death",
            "deny all axioms",
        ]
        return any(phrase in text for phrase in contradiction_phrases)
