"""
ApiKey Entity for Identity Bounded Context.

Represents an API key credential belonging to a User.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp, UserId


class ApiKey(Entity):
    """ApiKey Entity owned by a User aggregate.

    Attributes:
        user_id: UserId owning this API key.
        key_hash: Hashed secret key.
        prefix: Truncated public key prefix (e.g. 'vf_live_123').
        expires_at: Expiration timestamp (optional).
        scopes: List of permitted scope strings.
    """

    def __init__(
        self,
        id: EntityId,
        user_id: UserId,
        key_hash: str,
        prefix: str,
        scopes: Sequence[str],
        created_at: Timestamp | None = None,
        expires_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not key_hash or not isinstance(key_hash, str):
            raise ValueError("ApiKey key_hash cannot be empty")
        if not prefix or not isinstance(prefix, str):
            raise ValueError("ApiKey prefix cannot be empty")

        self._user_id = user_id
        self._key_hash = key_hash
        self._prefix = prefix
        self._scopes = tuple(scopes)
        self._expires_at = expires_at

    @property
    def user_id(self) -> UserId:
        """Get the owning user ID."""
        return self._user_id

    @property
    def key_hash(self) -> str:
        """Get the hashed key string."""
        return self._key_hash

    @property
    def prefix(self) -> str:
        """Get the public key prefix."""
        return self._prefix

    @property
    def scopes(self) -> tuple[str, ...]:
        """Get tuple of authorized API key scopes."""
        return self._scopes

    @property
    def expires_at(self) -> Timestamp | None:
        """Get expiration timestamp, or None if perpetual."""
        return self._expires_at

    def is_expired(self, current_time: Timestamp | None = None) -> bool:
        """Check if key has expired relative to current time."""
        if self._expires_at is None:
            return False
        now = current_time or Timestamp.now()
        return now.value >= self._expires_at.value
