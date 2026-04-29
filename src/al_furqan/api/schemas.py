"""Al-Furqan API Schemas — Pydantic v2 models for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional  # pylint: disable=wrong-import-order
from enum import Enum  # pylint: disable=wrong-import-order
from datetime import datetime  # pylint: disable=wrong-import-order


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────


class SystemTypeEnum(str, Enum):
    """Classification of the societal system a framework belongs to."""

    economic = "economic"  # pylint: disable=invalid-name
    social = "social"  # pylint: disable=invalid-name
    spiritual = "spiritual"  # pylint: disable=invalid-name
    political = "political"  # pylint: disable=invalid-name
    legal = "legal"  # pylint: disable=invalid-name
    technological = "technological"  # pylint: disable=invalid-name
    environmental = "environmental"  # pylint: disable=invalid-name
    mixed = "mixed"  # pylint: disable=invalid-name


class GateResultEnum(str, Enum):
    """Binary outcome of a single gate evaluation."""

    survive = "Survive"  # pylint: disable=invalid-name
    fail = "Fail"  # pylint: disable=invalid-name


class VerdictStatusEnum(str, Enum):
    """Lifecycle status of a verdict through the review pipeline."""

    pending_review = "pending_review"  # pylint: disable=invalid-name
    approved = "approved"  # pylint: disable=invalid-name
    corrected = "corrected"  # pylint: disable=invalid-name
    rejected = "rejected"  # pylint: disable=invalid-name
    superseded = "superseded"  # pylint: disable=invalid-name
    needs_review = "needs_review"  # pylint: disable=invalid-name


class ReviewActionEnum(str, Enum):
    """Actions a reviewer can take on a verdict."""

    approve = "approve"  # pylint: disable=invalid-name
    correct = "correct"  # pylint: disable=invalid-name
    reject = "reject"  # pylint: disable=invalid-name


class RoleEnum(str, Enum):
    """API access roles with increasing privilege levels."""

    reader = "reader"  # pylint: disable=invalid-name
    reviewer = "reviewer"  # pylint: disable=invalid-name
    admin = "admin"  # pylint: disable=invalid-name


# ──────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────


class EvaluateRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Request body for submitting a framework/question for Al-Furqan evaluation."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Question or framework to evaluate against Islamic principles",
    )
    context: Optional[str] = Field(
        None,
        description="Additional context to guide the evaluation",
    )
    options: Optional[dict] = Field(
        default_factory=lambda: {
            "max_correction_passes": 5,
            "include_precedent": True,
            "auto_approve_threshold": None,
        },
        description="Evaluation options: max_correction_passes, include_precedent, auto_approve_threshold",  # pylint: disable=line-too-long
    )


class CriterionTestRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Request body for testing a single framework against the criterion."""

    framework_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Name of the framework to test",
    )
    framework_description: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Detailed description of the framework",
    )


class ReviewRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Request body for a reviewer to act on a verdict."""

    action: ReviewActionEnum = Field(
        ...,
        description="Review action to perform",
    )
    corrections: Optional[dict] = Field(
        None,
        description="Correction payload when action is 'correct'",
    )
    notes: Optional[str] = Field(
        None,
        description="Reviewer notes explaining the decision",
    )


class VerdictSearchRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Request body for semantic search across verdicts."""

    q: str = Field(
        ...,
        min_length=1,
        description="Search query string",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of results to return",
    )


# ──────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────


class GateScoreResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Score and result for a single evaluation gate."""

    name: str = Field(..., description="Gate name (e.g. 'Tawhid Gate', 'Justice Gate')")
    score: int = Field(..., ge=0, le=100, description="Gate score from 0 to 100")
    result: GateResultEnum = Field(
        ..., description="Whether the framework survived this gate"
    )
    reasoning: str = Field(..., description="Explanation of the score and result")


class VerdictResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Complete verdict returned after evaluation or retrieval."""

    id: str = Field(..., description="Unique verdict identifier")
    question: str = Field(..., description="Original question or framework evaluated")
    primary_system: SystemTypeEnum = Field(
        ..., description="Detected primary system type"
    )
    friction_points: list[str] = Field(
        ..., description="Identified friction points with Islamic principles"
    )  # pylint: disable=line-too-long
    gate_scores: list[GateScoreResponse] = Field(
        ..., description="Individual gate evaluation results"
    )  # pylint: disable=line-too-long
    origin_gate: GateResultEnum = Field(
        ..., description="Overall gate result (Survive/Fail)"
    )
    consequences_short_term: list[str] = Field(
        ..., description="Predicted short-term consequences"
    )
    consequences_long_term: list[str] = Field(
        ..., description="Predicted long-term consequences"
    )
    revised_reasoning: str = Field(
        ..., description="Final reasoning after correction passes"
    )
    final_judgment: str = Field(..., description="Conclusive judgment text")
    total_score: int = Field(..., description="Aggregate score across all gates")
    passes: int = Field(..., description="Number of correction passes performed")
    timestamp: float = Field(..., description="Unix timestamp of verdict creation")
    status: VerdictStatusEnum = Field(..., description="Current review status")
    criterion_test_result: Optional[str] = Field(
        None,
        description="Result of criterion test if applicable",
    )

    model_config = {"from_attributes": True}


class VerdictListResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Paginated list of verdicts."""

    verdicts: list[VerdictResponse] = Field(..., description="List of verdict objects")
    total: int = Field(..., description="Total number of verdicts matching the query")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=20, description="Number of items per page")


class EvaluationStatusResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Status of an async evaluation job."""

    verdict_id: str = Field(..., description="ID of the verdict being processed")
    status: str = Field(
        ...,
        description="Current status: 'processing', 'completed', or 'failed'",
    )
    progress: Optional[str] = Field(
        None,
        description="Human-readable progress indicator",
    )
    verdict: Optional[VerdictResponse] = Field(
        None,
        description="The completed verdict (present only when status is 'completed')",
    )


class SearchResultResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """A single search result from the vector store."""

    id: str = Field(..., description="Document ID")
    document: str = Field(..., description="Document text content")
    score: float = Field(..., description="Relevance score")
    metadata: dict = Field(..., description="Associated metadata")


class StatsResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Aggregate statistics for the verdict store."""

    total_indexed: int = Field(
        ..., description="Total indexed documents in vector store"
    )
    total_files: int = Field(..., description="Total verdict files on disk")
    by_status: dict[str, int] = Field(
        ..., description="Verdict count grouped by status"
    )
    by_system: Optional[dict[str, int]] = Field(
        None,
        description="Verdict count grouped by system type",
    )
    accuracy_trend: Optional[list] = Field(
        None,
        description="Historical accuracy data points",
    )


class HealthResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """System health check response."""

    status: str = Field(..., description="Overall system status")
    llm_status: str = Field(..., description="LLM provider connectivity status")
    store_status: str = Field(..., description="Vector store connectivity status")
    version: str = Field(default="0.1.0", description="API version")


class ErrorResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Standard error response body."""

    detail: str = Field(..., description="Human-readable error message")
    error_code: Optional[str] = Field(
        None,
        description="Machine-readable error code",
    )


# ──────────────────────────────────────────────
# Auth Models
# ──────────────────────────────────────────────


class TokenResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """OAuth2-style token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token lifetime in seconds")


class APIKeyCreate(BaseModel):  # pylint: disable=too-few-public-methods
    """Request body to create a new API key."""

    name: str = Field(..., description="Human-readable name for the API key")
    role: RoleEnum = Field(
        default=RoleEnum.reader,
        description="Role to assign to the key",
    )


class APIKeyResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Response after creating an API key (key shown only once)."""

    key: str = Field(..., description="The generated API key (shown only on creation)")
    name: str = Field(..., description="Name of the API key")
    role: RoleEnum = Field(..., description="Assigned role")
    created_at: datetime = Field(..., description="Creation timestamp")
