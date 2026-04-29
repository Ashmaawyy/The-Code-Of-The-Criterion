"""Shared converter for turning raw verdict dicts into VerdictResponse objects."""

from al_furqan.api.schemas import (
    VerdictResponse,
    GateScoreResponse,
    GateResultEnum,
    VerdictStatusEnum,
)


def dict_to_verdict_response(
    data: dict, verdict_id: str | None = None
) -> VerdictResponse:
    """
    Convert a raw verdict dict (from JSON file or store) into a VerdictResponse.

    Handles edge cases: invalid enums fall back to defaults, missing fields
    get sensible zero-values.

    Args:
        data: Raw verdict dictionary.
        verdict_id: Override for the verdict ID. If None, uses data["id"].
    """
    resolved_id = verdict_id or data.get("id", "unknown")

    gate_scores = [
        GateScoreResponse(
            name=g.get("name", ""),
            score=g.get("score", 0),
            result=_safe_gate_result(g.get("result", "Fail")),
            reasoning=g.get("reasoning", ""),
        )
        for g in data.get("gate_scores", [])
    ]

    # Normalise status — handle unexpected values gracefully
    raw_status = data.get("status", "pending_review")
    try:
        verdict_status = VerdictStatusEnum(raw_status)
    except ValueError:
        verdict_status = VerdictStatusEnum.pending_review

    # Normalise origin gate
    origin_gate = _safe_gate_result(data.get("origin_gate", "Fail"))

    return VerdictResponse(
        id=resolved_id,
        question=data.get("question", ""),
        primary_system=data.get("primary_system", "mixed"),
        friction_points=data.get("friction_points", []),
        gate_scores=gate_scores,
        origin_gate=origin_gate,
        consequences_short_term=data.get("consequences_short_term", []),
        consequences_long_term=data.get("consequences_long_term", []),
        revised_reasoning=data.get("revised_reasoning", ""),
        final_judgment=data.get("final_judgment", ""),
        total_score=data.get("total_score", 0),
        passes=data.get("passes", 0),
        timestamp=data.get("timestamp", 0.0),
        status=verdict_status,
    )


def _safe_gate_result(value: str) -> GateResultEnum:
    """Parse a GateResultEnum, defaulting to Fail on invalid values."""
    try:
        return GateResultEnum(value)
    except ValueError:
        return GateResultEnum.Fail  # pylint: disable=no-member
