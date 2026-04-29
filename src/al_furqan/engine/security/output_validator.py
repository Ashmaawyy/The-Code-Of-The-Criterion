"""
Output Validator

Validates that engine output (verdicts and extractions) hasn't been
corrupted and conforms to expected structure and constraints.
"""

from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Result of an output validation check."""

    valid: bool
    issues: list[str] = field(default_factory=list)


EXPECTED_GATE_NAMES = frozenset(
    {
        "Source Integrity",
        "Structural Consistency",
        "Mediation Zeroing",
        "Origin Aware",
    }
)


class OutputValidator:
    """Validates that engine output hasn't been corrupted."""

    def validate_verdict(self, verdict) -> ValidationResult:  # pylint: disable=too-many-branches
        """Verify verdict structure and content integrity."""
        issues: list[str] = []

        # Must have gate_scores attribute
        if not hasattr(verdict, "gate_scores"):
            issues.append("Verdict missing gate_scores attribute")
            return ValidationResult(valid=False, issues=issues)

        gate_scores = verdict.gate_scores

        # Must have exactly 4 gate scores
        if len(gate_scores) != 4:
            issues.append(f"Expected 4 gates, got {len(gate_scores)}")

        # Gate names must match exactly
        actual_names = {g.name for g in gate_scores}
        missing = EXPECTED_GATE_NAMES - actual_names
        extra = actual_names - EXPECTED_GATE_NAMES
        if missing:
            issues.append(f"Missing gates: {missing}")
        if extra:
            issues.append(f"Unexpected gates: {extra}")

        # Scores in valid range
        for gate in gate_scores:
            if not hasattr(gate, "score"):
                issues.append(f"Gate {getattr(gate, 'name', '?')} missing score")
                continue
            if not (0 <= gate.score <= 100):  # pylint: disable=superfluous-parens
                issues.append(
                    f"Gate {gate.name} score {gate.score} out of range [0-100]"
                )

        # Total score should exist and be an int
        if hasattr(verdict, "total_score"):
            if not isinstance(verdict.total_score, (int, float)):
                issues.append(
                    f"total_score is not numeric: {type(verdict.total_score)}"
                )
        else:
            issues.append("Verdict missing total_score")

        # final_judgment should be non-empty
        if hasattr(verdict, "final_judgment"):
            if not verdict.final_judgment or not verdict.final_judgment.strip():
                issues.append("final_judgment is empty")
        else:
            issues.append("Verdict missing final_judgment")

        return ValidationResult(valid=len(issues) == 0, issues=issues)

    def validate_extraction(self, extraction: dict) -> ValidationResult:
        """Validate LLM extraction output has required fields."""
        required_fields = [
            "source_type",
            "is_verifiable",
            "contradicts_primary",
            "consistency_level",
            "foundation_type",
            "acknowledges_transcendence",
        ]

        issues: list[str] = []

        if not isinstance(extraction, dict):
            issues.append(f"Extraction is not a dict: {type(extraction)}")
            return ValidationResult(valid=False, issues=issues)

        for field_name in required_fields:
            if field_name not in extraction:
                issues.append(f"Missing required field: {field_name}")

        # Validate enum-like fields if present
        valid_source_types = {"primary", "secondary", "tertiary", "unknown"}
        if "source_type" in extraction:
            if extraction["source_type"] not in valid_source_types:
                issues.append(f"Invalid source_type: {extraction['source_type']}")

        valid_consistency = {"strong", "moderate", "weak", "contradictory", "unknown"}
        if "consistency_level" in extraction:
            if extraction["consistency_level"] not in valid_consistency:
                issues.append(
                    f"Invalid consistency_level: {extraction['consistency_level']}"
                )

        valid_foundation = {
            "transcendent",
            "rational",
            "empirical",
            "cultural",
            "unknown",
        }
        if "foundation_type" in extraction:
            if extraction["foundation_type"] not in valid_foundation:
                issues.append(
                    f"Invalid foundation_type: {extraction['foundation_type']}"
                )

        # Boolean fields
        for bool_field in [
            "is_verifiable",
            "contradicts_primary",
            "acknowledges_transcendence",
        ]:
            if bool_field in extraction and not isinstance(
                extraction[bool_field], bool
            ):
                issues.append(
                    f"{bool_field} should be bool, got {type(extraction[bool_field])}"
                )

        return ValidationResult(valid=len(issues) == 0, issues=issues)
