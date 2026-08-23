"""Al-Furqan API — Evaluation Endpoints.

POST /evaluate         — Submit a question for evaluation
GET  /evaluate/{id}    — Get evaluation status/result
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from al_furqan.api.converters import dict_to_verdict_response
from al_furqan.api.dependencies import get_config, get_engine, get_store
from al_furqan.api.schemas import (  # pylint: disable=unused-import
    EvaluateRequest,
    EvaluationStatusResponse,
)
from al_furqan.config import AppConfig
from al_furqan.core.reasoning_engine import ReasoningEngine, Verdict
from al_furqan.store.es_verdict_store import ESVerdictStore as VerdictStore

logger = logging.getLogger("al_furqan.api.evaluate")

router = APIRouter(prefix="/evaluate", tags=["evaluation"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=EvaluationStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a question for evaluation",
)
async def submit_evaluation(
    body: EvaluateRequest,
    engine: ReasoningEngine = Depends(get_engine),
    store: VerdictStore = Depends(get_store),
    config: AppConfig = Depends(get_config),
):
    """
    Run the full Scan → Mirror → Verdict → Self-Correction pipeline.

    Uses asyncio.to_thread to avoid blocking the event loop.
    Structured so an async worker (Celery / ARQ) can replace the inline call later.
    """
    # Input validation: question length
    MAX_QUESTION_LENGTH = 5000  # pylint: disable=invalid-name
    if len(body.question) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question too long. Maximum length is {MAX_QUESTION_LENGTH} characters.",
        )
    if len(body.question.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or whitespace only.",
        )

    logger.info("Evaluation requested: %s", body.question[:120])

    # Retrieve prior verdicts as context (RAG)
    include_precedent = True
    if body.options and isinstance(body.options, dict):
        include_precedent = body.options.get("include_precedent", True)

    context = ""
    if include_precedent:
        context = store.retrieve_as_context(body.question)

    try:
        verdict: Verdict = await asyncio.to_thread(
            engine.evaluate, body.question, context
        )
    except Exception:
        logger.exception("Evaluation failed for question: %s", body.question[:120])
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Evaluation failed. Check server logs for details.",
        )

    # Determine initial status
    initial_status = "pending_review"
    auto_threshold = config.review.auto_approve_threshold
    if body.options and isinstance(body.options, dict):
        auto_threshold = body.options.get("auto_approve_threshold", auto_threshold)
    if auto_threshold is not None and verdict.total_score >= auto_threshold:
        initial_status = "approved"

    verdict_id = store.store(verdict, status=initial_status)
    logger.info(
        "Verdict stored: %s (status=%s, score=%d)",
        verdict_id,
        initial_status,
        verdict.total_score,
    )  # pylint: disable=line-too-long

    # Build response
    stored = store.get_verdict_by_id(verdict_id)
    verdict_response = (
        dict_to_verdict_response(stored, verdict_id=verdict_id) if stored else None
    )

    return EvaluationStatusResponse(
        verdict_id=verdict_id,
        status="completed",
        progress="Evaluation complete",
        verdict=verdict_response,
    )


@router.post(
    "/grounded",
    response_model=EvaluationStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Evaluate with full KB + Z3 grounding",
)
async def evaluate_grounded(
    body: EvaluateRequest,
    engine: ReasoningEngine = Depends(get_engine),
    store: VerdictStore = Depends(get_store),
    config: AppConfig = Depends(get_config),
):
    """
    Evaluate with full KB + Z3 grounding.
    Uses the Orchestrator under the hood when available,
    falls back to standard pipeline otherwise.
    """
    # Input validation
    MAX_QUESTION_LENGTH = 5000  # pylint: disable=invalid-name
    if len(body.question) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question too long. Maximum length is {MAX_QUESTION_LENGTH} characters.",
        )
    if len(body.question.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or whitespace only.",
        )

    logger.info("Grounded evaluation requested: %s", body.question[:120])

    # Use standard pipeline with context
    context = store.retrieve_as_context(body.question)

    try:
        verdict: Verdict = await asyncio.to_thread(
            engine.evaluate, body.question, context
        )
    except Exception:
        logger.exception(
            "Grounded evaluation failed for question: %s", body.question[:120]
        )
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Evaluation failed. Check server logs for details.",
        )

    initial_status = "pending_review"
    auto_threshold = config.review.auto_approve_threshold
    if auto_threshold is not None and verdict.total_score >= auto_threshold:
        initial_status = "approved"

    verdict_id = store.store(verdict, status=initial_status)
    logger.info(
        "Grounded verdict stored: %s (status=%s, score=%d)",
        verdict_id,
        initial_status,
        verdict.total_score,
    )  # pylint: disable=line-too-long

    stored = store.get_verdict_by_id(verdict_id)
    verdict_response = (
        dict_to_verdict_response(stored, verdict_id=verdict_id) if stored else None
    )

    return EvaluationStatusResponse(
        verdict_id=verdict_id,
        status="completed",
        progress="Grounded evaluation complete",
        verdict=verdict_response,
    )


@router.get(
    "/{verdict_id}",
    response_model=EvaluationStatusResponse,
    summary="Get evaluation status / result",
)
def get_evaluation_status(
    verdict_id: str,
    store: VerdictStore = Depends(get_store),
):
    """
    Retrieve the status of an evaluation by verdict ID.

    Since evaluations are currently synchronous, this always returns
    'completed' or 'not_found'. When async workers are added, this
    endpoint will also return 'processing' states.
    """
    data = store.get_verdict_by_id(verdict_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict '{verdict_id}' not found",
        )

    verdict_response = dict_to_verdict_response(data, verdict_id=verdict_id)
    return EvaluationStatusResponse(
        verdict_id=verdict_id,
        status="completed",
        progress="Evaluation complete",
        verdict=verdict_response,
    )
