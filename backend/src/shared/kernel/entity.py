"""
Base Entity for Domain-Driven Design (DDD).

Defines the abstract base `Entity[TId]` class. Entities are identified by their identity
rather than their attribute values.
"""

from __future__ import annotations

from typing import TypeVar

from shared.kernel.value_objects import EntityId, Timestamp

TId = TypeVar("TId", bound=EntityId)


class Entity[TId: EntityId]:
    """Base class for all domain entities.

    Enforces identity-based equality, immutability of identity, and encapsulation
    of creation timestamp.
    """

    def __init__(self, id: TId, created_at: Timestamp | None = None) -> None:
        """Initialize a domain Entity.

        Args:
            id: Unique immutable typed identifier for the entity.
            created_at: Timestamp when the entity was created.
        """
        if id is None:
            raise ValueError("Entity ID cannot be None")

        self._id: TId = id
        self._created_at: Timestamp = created_at if created_at is not None else Timestamp.now()

    @property
    def id(self) -> TId:
        """Get the entity's unique immutable identifier."""
        return self._id

    @property
    def created_at(self) -> Timestamp:
        """Get the entity creation timestamp."""
        return self._created_at

    def __eq__(self, other: object) -> bool:
        """Entities are equal if and only if they share the exact same class and ID."""
        if not isinstance(other, Entity):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        """Hash based on immutable entity ID."""
        return hash(self._id)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self._id!r}, created_at={self._created_at!r})>"
