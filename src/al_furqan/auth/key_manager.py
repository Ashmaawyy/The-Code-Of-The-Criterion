"""API Key management — create, validate, revoke, rotate keys.

Keys are stored in a JSON file at the configured location (default: ~/.al-furqan/api_keys.json).
Each key is hashed with bcrypt before storage; the raw key is returned only at creation time.
"""

import json
import logging
import os
import secrets
import time
from pathlib import Path

import bcrypt

from al_furqan.auth.models import APIKey

logger = logging.getLogger("al_furqan.auth.key_manager")

# Key format: afk_live_{32 hex chars}
KEY_PREFIX = "afk_live_"
KEY_RANDOM_LENGTH = 32  # characters of random hex


class KeyManager:
    """Manages API key lifecycle: creation, validation, revocation, rotation."""

    def __init__(self, storage_path: str | None = None):
        if storage_path:
            self.storage_path = Path(storage_path).expanduser()
        else:
            self.storage_path = Path.home() / ".al-furqan" / "api_keys.json"
        self._keys: dict[str, APIKey] = {}
        self._load()

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load keys from disk."""
        if not self.storage_path.exists():
            self._keys = {}
            return
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                raw = json.load(f)
            self._keys = {k: APIKey.from_dict(v) for k, v in raw.items()}
            logger.info(
                "Loaded %d API key(s) from %s", len(self._keys), self.storage_path
            )
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load API keys from %s: %s", self.storage_path, exc)
            self._keys = {}

    def _save(self) -> None:
        """Persist keys to disk atomically."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.storage_path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(
                    {k: v.to_dict() for k, v in self._keys.items()},
                    f,
                    indent=2,
                )
            tmp_path.replace(self.storage_path)
            # Restrict permissions (owner read/write only)
            os.chmod(self.storage_path, 0o600)
        except OSError as exc:
            logger.error("Failed to save API keys: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Key Generation
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_raw_key() -> str:
        """Generate a new raw API key string."""
        random_part = secrets.token_hex(
            KEY_RANDOM_LENGTH // 2
        )  # 16 bytes = 32 hex chars
        return f"{KEY_PREFIX}{random_part}"

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        """Hash a raw API key with bcrypt."""
        return bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def _verify_key(raw_key: str, key_hash: str) -> bool:
        """Verify a raw key against its bcrypt hash."""
        try:
            return bcrypt.checkpw(raw_key.encode("utf-8"), key_hash.encode("utf-8"))
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_key(
        self, name: str, role: str = "reader", rate_limit: int = 0
    ) -> tuple[str, APIKey]:  # pylint: disable=line-too-long
        """
        Create a new API key.

        Returns:
            (raw_key, api_key_object) — raw_key is shown only once.
        """
        if role not in APIKey.ROLES:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {APIKey.ROLES}")

        raw_key = self._generate_raw_key()
        key_hash = self._hash_key(raw_key)
        key_id = raw_key[: len(KEY_PREFIX) + 8]  # e.g. "afk_live_a1b2c3d4"

        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            role=role,
            created_at=time.time(),
            rate_limit=rate_limit,
        )

        self._keys[key_id] = api_key
        self._save()
        logger.info("Created API key '%s' (role=%s) → %s", name, role, key_id)
        return raw_key, api_key

    def validate_key(self, raw_key: str) -> APIKey | None:
        """
        Validate a raw API key. Returns the APIKey if valid and active, else None.
        Also updates last_used timestamp.
        """
        if not raw_key or not raw_key.startswith(KEY_PREFIX):
            return None

        for key_id, api_key in self._keys.items():  # pylint: disable=unused-variable
            if not api_key.is_active:
                continue
            if self._verify_key(raw_key, api_key.key_hash):
                api_key.last_used = time.time()
                self._save()
                return api_key
        return None

    def revoke_key(self, key_id: str) -> bool:
        """Revoke (deactivate) a key by its key_id."""
        if key_id not in self._keys:
            return False
        self._keys[key_id].is_active = False
        self._save()
        logger.info("Revoked API key: %s", key_id)
        return True

    def rotate_key(self, key_id: str) -> tuple[str, APIKey] | None:
        """
        Rotate a key: revoke the old one, create a new one with the same name/role.
        Returns (new_raw_key, new_api_key) or None if key_id not found.
        """
        old_key = self._keys.get(key_id)
        if not old_key:
            return None

        # Revoke old
        old_key.is_active = False

        # Create new with same settings
        raw_key, new_key = self.create_key(
            name=old_key.name,
            role=old_key.role,
            rate_limit=old_key.rate_limit,
        )
        logger.info("Rotated key %s → %s", key_id, new_key.key_id)
        return raw_key, new_key

    def list_keys(self) -> list[APIKey]:
        """List all keys (active and inactive)."""
        return list(self._keys.values())

    def get_key(self, key_id: str) -> APIKey | None:
        """Get a key by its key_id."""
        return self._keys.get(key_id)
