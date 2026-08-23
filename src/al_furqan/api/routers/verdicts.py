"""Al-Furqan API — Verdict CRUD Endpoints.

GET    /verdicts           — List verdicts with filters
GET    /verdicts/search    — Semantic search
GET    /verdicts/{id}      — Get single verdict
DELETE /verdicts/{id}      — Invalidate with cascade
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status

from al_furqan.api.dependencies import get_store
from al_furqan.api.schemas import (
    GateResultEnum,
    GateScoreResponse,
    SearchResultResponse,
    SystemTypeEnum,
    VerdictListResponse,
    VerdictResponse,
    VerdictStatusEnum,
)
from al_furqan.store.es_verdict_store import ESVerdictStore as VerdictStore

logger = logging.getLogger("al_furqan.api.verdicts")

router = APIRouter(prefix="/verdicts", tags=["verdicts"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dict_to_verdict_response(data: dict) -> VerdictResponse:
    """Convert a raw verdict dict (from JSON file) into a VerdictResponse."""
    gate_scores = [
        GateScoreResponse(
            name=g.get("name", ""),
            score=g.get("score", 0),
            result=GateResultEnum(g.get("result", "Fail")),
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

    # Normalise system type
    raw_system = data.get("primary_system", "mixed")
    try:
        system_type = SystemTypeEnum(raw_system)
    except ValueError:
        system_type = SystemTypeEnum.mixed

    return VerdictResponse(
        id=data.get("id", "unknown"),
        question=data.get("question", ""),
        primary_system=system_type,
        friction_points=data.get("friction_points", []),
        gate_scores=gate_scores,
        origin_gate=GateResultEnum(data.get("origin_gate", "Fail")),
        consequences_short_term=data.get("consequences_short_term", []),
        consequences_long_term=data.get("consequences_long_term", []),
        revised_reasoning=data.get("revised_reasoning", ""),
        final_judgment=data.get("final_judgment", ""),
        total_score=data.get("total_score", 0),
        passes=data.get("passes", 0),
        timestamp=data.get("timestamp", 0.0),
        status=verdict_status,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/search",
    response_model=list[SearchResultResponse],
    summary="Semantic search across verdicts",
)
def search_verdicts(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=5, ge=1, le=50, description="Max results"),
    store: VerdictStore = Depends(get_store),
):
    """Search past verdicts by semantic similarity using the vector store."""
    logger.info("Verdict search: q=%r limit=%d", q, limit)
    results = store.retrieve(q, n_results=limit)
    return [
        SearchResultResponse(
            id=r["id"],
            document=r.get("document", ""),
            score=r.get("distance", 0.0),
            metadata=r.get("metadata", {}),
        )
        for r in results
    ]


@router.get(
    "",
    response_model=VerdictListResponse,
    summary="List verdicts with filters",
)
def list_verdicts(
    status_filter: str | None = Query(
        None, alias="status", description="Filter by status"
    ),
    system_type: str | None = Query(None, description="Filter by primary_system"),
    limit: int = Query(default=20, ge=1, le=100, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    store: VerdictStore = Depends(get_store),
):
    """
    List verdicts from JSON files on disk (not just ChromaDB).

    Supports filtering by status and system_type, with pagination.
    Results are sorted by timestamp descending (newest first).
    """
    logger.info(
        "List verdicts: status=%s system=%s limit=%d offset=%d",
        status_filter,
        system_type,
        limit,
        offset,
    )

    verdicts_dir: Path = store.verdicts_dir
    all_verdicts: list[dict] = []

    for path in verdicts_dir.glob("*.json"):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skipping corrupt verdict file %s: %s", path.name, exc)
            continue

        # Apply filters
        if status_filter and data.get("status") != status_filter:
            continue
        if system_type and data.get("primary_system") != system_type:
            continue

        all_verdicts.append(data)

    # Sort by timestamp descending
    all_verdicts.sort(key=lambda v: v.get("timestamp", 0), reverse=True)

    total = len(all_verdicts)
    page_data = all_verdicts[offset : offset + limit]

    return VerdictListResponse(
        verdicts=[_dict_to_verdict_response(d) for d in page_data],
        total=total,
        page=(offset // limit) + 1 if limit else 1,
        per_page=limit,
    )


@router.get(
    "/{verdict_id}",
    response_model=VerdictResponse,
    summary="Get a single verdict by ID",
)
def get_verdict(
    verdict_id: str,
    store: VerdictStore = Depends(get_store),
):
    """Retrieve a single verdict by its ID."""
    logger.info("Get verdict: %s", verdict_id)
    data = store.get_verdict_by_id(verdict_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict '{verdict_id}' not found",
        )
    return _dict_to_verdict_response(data)


@router.delete(
    "/{verdict_id}",
    summary="Invalidate a verdict with cascade",
    status_code=status.HTTP_200_OK,
)
def invalidate_verdict(
    verdict_id: str,
    store: VerdictStore = Depends(get_store),
):
    """
    Invalidate a verdict and cascade-flag any downstream verdicts
    that may have used it as precedent.
    """
    logger.info("Invalidate verdict: %s", verdict_id)

    data = store.get_verdict_by_id(verdict_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict '{verdict_id}' not found",
        )

    flagged = store.invalidate_cascade(verdict_id)
    logger.info(
        "Verdict %s invalidated. Flagged %d downstream.", verdict_id, len(flagged)
    )

    return {
        "verdict_id": verdict_id,
        "status": "invalidated",
        "flagged_for_review": flagged,
        "flagged_count": len(flagged),
    }
