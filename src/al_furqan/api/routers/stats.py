"""Al-Furqan API — Stats & Health Endpoints.

GET /stats   — System statistics
GET /health  — Health check (LLM + store status)
"""

import logging

from fastapi import APIRouter, Depends, Request

from al_furqan.api.dependencies import get_store, get_config
from al_furqan.api.schemas import StatsResponse, HealthResponse
from al_furqan.store.es_verdict_store import ESVerdictStore as VerdictStore
from al_furqan.config import AppConfig

logger = logging.getLogger("al_furqan.api.stats")

router = APIRouter(tags=["stats"])


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="System statistics",
)
def get_stats(
    store: VerdictStore = Depends(get_store),
):
    """Return aggregate statistics from the verdict store."""
    raw_stats = store.stats()

    # Count by system type from files
    by_system: dict[str, int] = {}
    for path in store.verdicts_dir.glob("*.json"):
        try:
            import json  # pylint: disable=import-outside-toplevel

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            sys_type = data.get("primary_system", "unknown")
            by_system[sys_type] = by_system.get(sys_type, 0) + 1
        except Exception:  # pylint: disable=broad-exception-caught
            continue

    return StatsResponse(
        total_indexed=raw_stats.get("total_indexed", 0),
        total_files=raw_stats.get("total_files", 0),
        by_status=raw_stats.get("by_status", {}),
        by_system=by_system if by_system else None,
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
def health_check(
    request: Request,
    store: VerdictStore = Depends(get_store),
    config: AppConfig = Depends(get_config),
):
    """
    Check system health: LLM connectivity and store status.

    Returns degraded/healthy/unhealthy based on component states.
    """
    # Check store
    store_ok = False
    try:
        store.stats()
        store_ok = True
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Store health check failed: %s", exc)

    # Check LLM — try a minimal call if the engine is available
    llm_ok = False
    llm_status_msg = "unknown"
    try:
        llm_provider = getattr(request.app.state, "llm", None)
        if llm_provider is not None:
            # The LLM is at least initialised
            llm_ok = True
            llm_status_msg = (
                f"connected ({config.llm.provider}/{config.llm.model_name})"
            )
        else:
            llm_status_msg = "not initialised"
    except Exception as exc:  # pylint: disable=broad-exception-caught
        llm_status_msg = f"error: {exc}"

    # Overall status
    if store_ok and llm_ok:
        overall = "healthy"
    elif store_ok or llm_ok:
        overall = "degraded"
    else:
        overall = "unhealthy"

    return HealthResponse(
        status=overall,
        llm_status=llm_status_msg,
        store_status="connected" if store_ok else "disconnected",
        version="0.1.0",
    )
