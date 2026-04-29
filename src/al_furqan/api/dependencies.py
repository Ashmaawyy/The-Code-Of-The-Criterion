"""Shared FastAPI dependencies for dependency injection."""

from fastapi import Request
from al_furqan.core.reasoning_engine import ReasoningEngine
from al_furqan.store.es_verdict_store import ESVerdictStore as VerdictStore
from al_furqan.config import AppConfig


def get_store(request: Request) -> VerdictStore:
    """Retrieve the VerdictStore instance from app state."""
    return request.app.state.store


def get_engine(request: Request) -> ReasoningEngine:
    """Retrieve the ReasoningEngine instance from app state."""
    return request.app.state.engine


def get_config(request: Request) -> AppConfig:
    """Retrieve the AppConfig instance from app state."""
    return request.app.state.config
