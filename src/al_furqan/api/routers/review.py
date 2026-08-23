"""Al-Furqan API — Human Review Endpoint.

POST /verdicts/{verdict_id}/review — Submit a review action (approve/correct/reject)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from al_furqan.api.dependencies import get_store
from al_furqan.api.schemas import ReviewActionEnum, ReviewRequest
from al_furqan.core.reasoning_engine import Verdict
from al_furqan.store.es_verdict_store import ESVerdictStore as VerdictStore

logger = logging.getLogger("al_furqan.api.review")

router = APIRouter(prefix="/verdicts", tags=["review"])


@router.post(
    "/{verdict_id}/review",
    summary="Submit a human review for a verdict",
    status_code=status.HTTP_200_OK,
)
def submit_review(  # pylint: disable=inconsistent-return-statements
    verdict_id: str,
    body: ReviewRequest,
    store: VerdictStore = Depends(get_store),
):
    """
    Human reviewer submits an action on a verdict:
    - **approve**: Mark as sound, re-index for future precedent.
    - **correct**: Provide corrections; stores corrected version, supersedes original.
    - **reject**: Mark as unsound, remove from precedent index.
    """
    logger.info("Review submitted for %s: action=%s", verdict_id, body.action.value)

    data = store.get_verdict_by_id(verdict_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict '{verdict_id}' not found",
        )

    if body.action == ReviewActionEnum.approve:  # pylint: disable=no-else-return
        success = store.update_status(verdict_id, "approved")
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update verdict status",
            )
        logger.info("Verdict %s approved", verdict_id)
        return {
            "verdict_id": verdict_id,
            "action": "approved",
            "message": "Verdict approved and indexed for precedent.",
        }

    elif body.action == ReviewActionEnum.reject:
        success = store.update_status(verdict_id, "rejected")
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update verdict status",
            )

        # Append reviewer notes via ES update
        if body.notes and hasattr(store, "_es"):
            store._es.update(
                index=store._index,
                id=verdict_id,
                body={"doc": {"rejection_reason": body.notes}},
                refresh="wait_for",
            )

        logger.info("Verdict %s rejected", verdict_id)
        return {
            "verdict_id": verdict_id,
            "action": "rejected",
            "message": "Verdict rejected and removed from precedent index.",
        }

    elif body.action == ReviewActionEnum.correct:
        if not body.corrections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrections payload required when action is 'correct'",
            )

        # Build a corrected Verdict from the original + corrections overlay
        try:
            corrected_data = {**data, **body.corrections}
            corrected_verdict = Verdict.from_dict(corrected_data)
        except Exception:
            logger.exception("Failed to build corrected verdict")
            raise HTTPException(  # pylint: disable=raise-missing-from
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid corrections payload. Check server logs for details.",
            )

        success = store.update_status(
            verdict_id,
            "corrected",
            corrected_verdict=corrected_verdict,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store corrected verdict",
            )

        logger.info("Verdict %s corrected", verdict_id)
        return {
            "verdict_id": verdict_id,
            "action": "corrected",
            "message": "Original superseded. Corrected verdict stored and indexed.",
        }
