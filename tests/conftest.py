"""
Shared fixtures for Al-Furqan unit tests.
"""

import json
import logging
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from al_furqan import LOG_DATEFMT, LOG_FORMAT
from al_furqan.auth.key_manager import KeyManager
from al_furqan.core.reasoning_engine import (
    GateResult,
    GateScore,
    ReasoningEngine,
    SystemType,
    Verdict,
)
from al_furqan.store.es_verdict_store import ESVerdictStore as VerdictStore

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------


def pytest_configure(config):  # pylint: disable=unused-argument
    """Set up logging for all tests. Use `pytest --log-cli-level=INFO` to see output."""
    logging.basicConfig(
        level=logging.DEBUG, format=LOG_FORMAT, datefmt=LOG_DATEFMT, force=True
    )


logger = logging.getLogger("conftest")

# pylint: disable=redefined-outer-name


# ---------------------------------------------------------------------------
# Mock LLM Responses
# ---------------------------------------------------------------------------

MOCK_SCAN_RESPONSE = json.dumps(
    {
        "primary_system": "economic",
        "immediate_effects": ["Wealth concentration", "Debt accumulation"],
        "network_effects": ["Systemic inequality", "Erosion of social trust"],
        "friction_points": [
            "Interest-based lending contradicts equitable wealth distribution",
            "Debt compounding violates network effect axiom",
        ],
    }
)

MOCK_MIRROR_RESPONSE = json.dumps(
    {
        "gate_1_source_integrity": {
            "score": 85,
            "result": "Survive",
            "reasoning": "Data on interest-based lending effects is well-documented.",
        },
        "gate_2_structural_consistency": {
            "score": 70,
            "result": "Survive",
            "reasoning": "Causal chain from interest to inequality is traceable.",
        },
        "gate_3_mediation_zeroing": {
            "score": 90,
            "result": "Survive",
            "reasoning": "Analysis does not rely on human preference as foundation.",
        },
        "gate_4_origin_aware": {
            "score": 80,
            "result": "Survive",
            "reasoning": "Prohibition of interest is derived from transcendent source.",
        },
        "contradictions_found": [],
        "axiom_alignment_notes": "Fully aligned with core axioms.",
    }
)

MOCK_VERDICT_RESPONSE = json.dumps(
    {
        "consequences_short_term": ["Increased household debt", "Reduced savings"],
        "consequences_long_term": ["Widening wealth gap", "Social instability"],
        "actors_and_mechanisms": "Lenders profit; borrowers bear compounding risk.",
        "revised_reasoning": "Interest-based lending creates systemic debt traps.",
        "final_judgment": "Interest-based lending violates design principles of equitable exchange.",
        "total_score": 85,
    }
)

MOCK_CORRECTION_SOUND = json.dumps(
    {
        "contradictions_found": [],
        "is_sound": True,
        "corrected_verdict": None,
    }
)

MOCK_CORRECTION_WITH_FIX = json.dumps(
    {
        "contradictions_found": ["Score should be higher given full gate survival"],
        "is_sound": False,
        "corrected_verdict": {
            "consequences_short_term": ["Increased household debt", "Reduced savings"],
            "consequences_long_term": ["Widening wealth gap", "Social instability"],
            "actors_and_mechanisms": (
                "Lenders profit; borrowers bear compounding risk."
            ),
            "revised_reasoning": (
                "Interest-based lending creates systemic debt traps."
            ),
            "final_judgment": (
                "Interest-based lending violates design"
                " principles of equitable exchange."
            ),
            "total_score": 90,
        },
    }
)


def make_mock_llm(responses: list[str] | None = None):
    """
    Create a mock LLM callable that returns predefined responses in sequence.
    If no responses given, uses the default Scan → Mirror → Verdict → Correction flow.
    """
    if responses is None:
        responses = [
            MOCK_SCAN_RESPONSE,
            MOCK_MIRROR_RESPONSE,
            MOCK_VERDICT_RESPONSE,
            MOCK_CORRECTION_SOUND,
        ]
    call_count = {"n": 0}
    logger.info("Mock LLM created with %d response(s)", len(responses))

    def mock_llm(prompt: str) -> str:
        idx = min(call_count["n"], len(responses) - 1)
        call_count["n"] += 1
        logger.debug(
            "Mock LLM call #%d — prompt length=%d, returning response #%d",
            call_count["n"],
            len(prompt),
            idx + 1,
        )
        return responses[idx]

    return mock_llm


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_llm():
    """Default mock LLM that returns a full Scan→Mirror→Verdict→Correction flow."""
    logger.info("Creating default mock LLM (Scan→Mirror→Verdict→Correction)")
    return make_mock_llm()


@pytest.fixture
def engine(mock_llm):
    """ReasoningEngine wired to a mock LLM."""
    logger.info("Creating ReasoningEngine with mock LLM")
    return ReasoningEngine(mock_llm)


@pytest.fixture
def sample_verdict():
    """A fully populated Verdict object for testing."""
    logger.info("Building sample_verdict fixture (interest-based lending, score=85)")
    return Verdict(
        question="Is interest-based lending just?",
        primary_system=SystemType.ECONOMIC,
        friction_points=[
            "Interest contradicts equitable exchange",
            "Debt compounding harms borrowers",
        ],
        gate_scores=[
            GateScore(
                "Source-Integrity", 85, GateResult.SURVIVE, "Data is well-documented."
            ),
            GateScore(
                "Structural-Consistency",
                70,
                GateResult.SURVIVE,
                "Causal chain traceable.",
            ),
            GateScore(
                "Mediation-Zeroing",
                90,
                GateResult.SURVIVE,
                "No human preference reliance.",
            ),
        ],
        origin_gate=GateResult.SURVIVE,
        consequences_short_term=["Increased debt", "Reduced savings"],
        consequences_long_term=["Wealth gap", "Instability"],
        revised_reasoning="Interest creates systemic debt traps.",
        final_judgment="Interest-based lending violates equitable exchange.",
        total_score=85,
        passes=1,
        timestamp=1700000000.0,
    )


@pytest.fixture
def tmp_store(tmp_path):
    """A VerdictStore backed by ES (requires ES running)."""
    try:
        from elasticsearch import Elasticsearch

        es = Elasticsearch(["http://localhost:9200"], request_timeout=5)
        if not es.ping():
            pytest.skip("Elasticsearch not available")
        # Use a unique test index
        test_index = f"furqan_verdicts_test_{tmp_path.name[-8:]}"
        from al_furqan.kb.es.indices import VERDICTS_INDEX

        if es.indices.exists(index=test_index):
            es.indices.delete(index=test_index)
        es.indices.create(index=test_index, body=VERDICTS_INDEX)
        store = VerdictStore(es=es, index=test_index)
        yield store
        es.indices.delete(index=test_index, ignore=[404])
    except Exception:
        pytest.skip("Elasticsearch not available")


@pytest.fixture
def tmp_key_manager(tmp_path):
    """A KeyManager using a temporary storage file."""
    storage_path = tmp_path / "api_keys.json"
    return KeyManager(storage_path=str(storage_path))


# ---------------------------------------------------------------------------
# FastAPI Test Client Fixtures
# ---------------------------------------------------------------------------


def _make_test_config(
    tmp_path,
    auth_enabled=False,
    key_storage=None,
):
    """Build a test AppConfig with temp directories."""
    from al_furqan.config import (  # pylint: disable=import-outside-toplevel
        APIConfig,
        AppConfig,
        AuthConfig,
        EngineConfig,
        ReviewConfig,
        StoreConfig,
    )

    # pylint: disable=import-outside-toplevel
    from al_furqan.providers.llm_layer import LLMConfig as _LLMConfig

    return AppConfig(
        llm=_LLMConfig(provider="ollama", model_name="test"),
        engine=EngineConfig(max_correction_passes=1),
        store=StoreConfig(
            backend="elasticsearch",
        ),
        review=ReviewConfig(),
        api=APIConfig(cors_origins=["http://localhost:3000"]),
        auth=AuthConfig(
            enabled=auth_enabled,
            key_storage=key_storage or str(tmp_path / "api_keys.json"),
        ),
    )


@pytest.fixture
def client_no_auth(tmp_path):
    """TestClient with auth disabled — for testing endpoint logic."""
    from al_furqan.api.app import create_app  # pylint: disable=import-outside-toplevel

    config = _make_test_config(tmp_path, auth_enabled=False)

    # Keep patch active through entire lifespan (create_app + TestClient enter/exit)
    with patch("al_furqan.api.app.load_config", return_value=config):
        app = create_app()
        mock_llm_fn = make_mock_llm()
        engine = ReasoningEngine(llm_call=mock_llm_fn)

        with TestClient(app) as client:
            app.state.engine = engine
            app.state.llm = mock_llm_fn
            yield client


@pytest.fixture
def auth_client(tmp_path):
    """TestClient with auth enabled.

    Returns (client, admin_raw_key, reader_raw_key,
    evaluator_raw_key).
    """
    from al_furqan.api.app import create_app  # pylint: disable=import-outside-toplevel

    config = _make_test_config(tmp_path, auth_enabled=True)

    with patch("al_furqan.api.app.load_config", return_value=config):
        app = create_app()
        mock_llm_fn = make_mock_llm()
        engine = ReasoningEngine(llm_call=mock_llm_fn)

        with TestClient(app) as client:
            app.state.engine = engine
            app.state.llm = mock_llm_fn

            km = app.state.key_manager
            admin_key, _ = km.create_key("test-admin", role="admin")
            reader_key, _ = km.create_key("test-reader", role="reader")
            evaluator_key, _ = km.create_key("test-evaluator", role="evaluator")

            yield client, admin_key, reader_key, evaluator_key
