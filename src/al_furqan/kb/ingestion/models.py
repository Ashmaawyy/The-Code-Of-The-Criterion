"""
Data models for the Knowledge Graph ingestion pipeline.

ProposedEdge represents a relationship extracted by the LLM that
awaits human review before entering the Knowledge Graph.
"""

from dataclasses import dataclass, asdict
import uuid


@dataclass
class ProposedEdge:  # pylint: disable=too-many-instance-attributes
    """
    A proposed knowledge graph edge awaiting human review.

    No edge enters the KG directly — all go through this staging model.
    """

    id: str
    lesson_id: str
    source_node: str
    target_node: str
    edge_type: str
    provenance: str
    provenance_type: str
    reference: str
    timestamp_start: str
    timestamp_end: str
    transcript_chunk: str
    llm_reasoning: str
    llm_confidence: float
    status: str = "pending"  # pending / confirmed / edited / rejected
    reviewed_by: str = ""
    review_notes: str = ""
    review_timestamp: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ProposedEdge":
        """Create from dictionary."""
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})  # pylint: disable=no-member

    @staticmethod
    def generate_id() -> str:
        """Generate a unique edge ID."""
        return str(uuid.uuid4())
