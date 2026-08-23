"""API Key data model for Al-Furqan authentication."""

import time
from dataclasses import asdict, dataclass, field


@dataclass
class APIKey:  # pylint: disable=too-many-instance-attributes
    """Represents a stored API key with metadata and permissions."""

    key_id: str  # Public prefix for identification (first 12 chars of key)
    key_hash: str  # bcrypt hash of the full key
    name: str  # Human-readable name ("Muhammad's key")
    role: str  # "reader" | "evaluator" | "admin"
    created_at: float = field(default_factory=time.time)
    last_used: float = 0.0
    is_active: bool = True
    rate_limit: int = 0  # Requests per minute (0 = use default)
    allowed_models: list[str] = field(default_factory=list)

    # Roles and their hierarchy
    ROLES = ("reader", "evaluator", "admin")

    # Role → permitted HTTP methods
    ROLE_PERMISSIONS = {
        "reader": {"GET"},
        "evaluator": {"GET", "POST"},
        "admin": {"GET", "POST", "PUT", "PATCH", "DELETE"},
    }

    def has_permission(self, method: str) -> bool:
        """Check if the key's role allows the given HTTP method."""
        allowed = self.ROLE_PERMISSIONS.get(self.role, set())
        return method.upper() in allowed

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "APIKey":
        """Deserialize from dict."""
        # Filter only known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}  # pylint: disable=no-member
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)
