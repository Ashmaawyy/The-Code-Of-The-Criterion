"""Al-Furqan API — Criterion Test Endpoint.

POST /criterion-test — Run the full Criterion Test on a named framework.
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from al_furqan.api.converters import dict_to_verdict_response
from al_furqan.api.dependencies import get_config, get_engine, get_store
from al_furqan.api.schemas import (  # pylint: disable=unused-import
    CriterionTestRequest,
    VerdictResponse,
)
from al_furqan.config import AppConfig
from al_furqan.core.reasoning_engine import ReasoningEngine, Verdict
from al_furqan.store.es_verdict_store import ESVerdictStore as VerdictStore

logger = logging.getLogger("al_furqan.api.criterion")

router = APIRouter(tags=["criterion"])


@router.post(
    "/criterion-test",
    response_model=VerdictResponse,
    summary="Run the full Criterion Test on a framework",
)
async def run_criterion_test(
    body: CriterionTestRequest,
    engine: ReasoningEngine = Depends(get_engine),
    store: VerdictStore = Depends(get_store),
    config: AppConfig = Depends(get_config),
):
    """
    Evaluate a named framework against the full Criterion.

    The framework name and description are combined into a structured question
    that the reasoning engine processes through all gates. The result includes
    a clear Survive/Fail outcome for the entire framework.
    """
    question = (
        f"Criterion Test for framework: {body.framework_name}\n\n"
        f"Description: {body.framework_description}\n\n"
        f"Evaluate this framework against all axioms and gates of The Criterion. "
        f"Determine whether the framework survives or fails each gate, and deliver "
        f"a final judgment on the framework as a whole."
    )

    logger.info("Criterion test requested: %s", body.framework_name)

    context = store.retrieve_as_context(question)

    try:
        verdict: Verdict = await asyncio.to_thread(engine.evaluate, question, context)
    except Exception:
        logger.exception("Criterion test failed for: %s", body.framework_name)
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Criterion test failed. Check server logs for details.",
        )

    # Store with pending_review by default
    initial_status = "pending_review"
    auto_threshold = config.review.auto_approve_threshold
    if auto_threshold is not None and verdict.total_score >= auto_threshold:
        initial_status = "approved"

    verdict_id = store.store(verdict, status=initial_status)
    logger.info("Criterion test stored: %s (score=%d)", verdict_id, verdict.total_score)

    stored = store.get_verdict_by_id(verdict_id)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve stored verdict",
        )

    # Add criterion test metadata
    stored["criterion_test_result"] = (
        "SURVIVES" if verdict.total_score == 100 else "FAILS"
    )

    response = dict_to_verdict_response(stored, verdict_id=verdict_id)
    response.criterion_test_result = stored["criterion_test_result"]
    return response
