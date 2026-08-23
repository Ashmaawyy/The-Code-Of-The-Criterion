"""Al-Furqan API — Main FastAPI Application.

Initialises the LLM provider, verdict store, and reasoning engine on startup,
then exposes all API endpoints under /api/v1.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from al_furqan.api.routers import criterion, evaluate, review, stats, verdicts
from al_furqan.auth.errors import ErrorCode, error_response
from al_furqan.auth.key_manager import KeyManager
from al_furqan.auth.middleware import APIKeyMiddleware
from al_furqan.auth.security import BodySizeLimitMiddleware, SecurityHeadersMiddleware
from al_furqan.config import load_config
from al_furqan.core.reasoning_engine import ReasoningEngine
from al_furqan.kb.es.client import create_es_client
from al_furqan.providers.llm_layer import LLMProvider, create_llm
from al_furqan.store.es_verdict_store import ESVerdictStore as VerdictStore

logger = logging.getLogger("al_furqan.api")
# pylint: disable=broad-exception-caught
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument

# ---------------------------------------------------------------------------
# Lifespan — initialise / tear down shared resources
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI()):
    """Startup: create LLM, store, engine. Shutdown: cleanup."""
    logger.info("Al-Furqan API starting up…")

    # Load config
    config = load_config()
    app.state.config = config

    # Initialise Elasticsearch client + verdict store
    es_client = create_es_client(
        hosts=config.store.elasticsearch.hosts,
        request_timeout=config.store.elasticsearch.request_timeout,
    )
    app.state.es = es_client
    store = VerdictStore(es=es_client)
    app.state.store = store
    logger.info("VerdictStore ready (ES-backed)")

    # Initialise LLM provider
    try:
        llm: LLMProvider = create_llm(config.llm)
        app.state.llm = llm
        logger.info(
            "LLM provider ready: %s/%s", config.llm.provider, config.llm.model_name
        )

    except Exception as init_err:
        logger.warning(
            "LLM provider failed to initialise: %s — API will run in degraded mode",
            init_err,
        )

        # Provide a stub that raises on call so the app can still serve reads
        def _llm_stub(prompt: str, _err: Exception = init_err) -> str:
            raise RuntimeError(f"LLM not available: {_err}")

        llm = _llm_stub  # type: ignore
        app.state.llm = None

    # Initialise reasoning engine
    engine = ReasoningEngine(llm_call=llm)
    app.state.engine = engine
    logger.info("ReasoningEngine ready")

    yield  # ← application runs here

    logger.info("Al-Furqan API shutting down…")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Al-Furqan — The Criterion",
        description=(
            "Axiom-anchored AI reasoning framework. Evaluates ideas, policies, "
            "and behaviours against immutable axioms and survival gates."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    # -- Config --
    config = load_config()

    # -- Security Middlewares (outermost first) --
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(BodySizeLimitMiddleware, max_body_size=64 * 1024)

    # -- Auth Middleware --
    key_manager = KeyManager(storage_path=config.auth.key_storage)
    app.state.key_manager = key_manager
    app.add_middleware(
        APIKeyMiddleware,
        key_manager=key_manager,
        auth_enabled=config.auth.enabled,
    )

    # -- CORS --
    cors_origins = config.api.cors_origins
    cors_credentials = config.api.cors_allow_credentials
    # Never allow credentials with wildcard origins
    if "*" in cors_origins:
        cors_credentials = False
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -- Routers --
    app.include_router(evaluate.router, prefix="/api/v1")
    app.include_router(verdicts.router, prefix="/api/v1")
    app.include_router(review.router, prefix="/api/v1")
    app.include_router(criterion.router, prefix="/api/v1")
    app.include_router(stats.router, prefix="/api/v1")

    # -- Root health endpoint --
    @app.get("/", tags=["root"])
    def root():
        return {
            "name": "Al-Furqan — The Criterion",
            "version": "0.1.0",
            "docs": "/docs",
            "api": "/api/v1",
        }

    # -- Exception handlers (structured error format) --
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning("ValueError on %s %s: %s", request.method, request.url.path, exc)
        return error_response(400, ErrorCode.BAD_REQUEST, str(exc))

    @app.exception_handler(RuntimeError)
    async def runtime_error_handler(request: Request, exc: RuntimeError):
        logger.error("RuntimeError on %s %s: %s", request.method, request.url.path, exc)
        return error_response(500, ErrorCode.INTERNAL_ERROR, "Internal server error")

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        logger.exception(
            "Unhandled exception on %s %s", request.method, request.url.path
        )
        return error_response(500, ErrorCode.INTERNAL_ERROR, "Internal server error")

    return app


# Module-level app instance for `uvicorn al_furqan.api.app:app`
app = create_app()
