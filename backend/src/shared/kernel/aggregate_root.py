"""
AggregateRoot Base Implementation.

Defines the transactional boundary for domain entities and encapsulates domain events.
"""

from __future__ import annotations

from typing import TypeVar

from shared.kernel.domain_event import DomainEvent
from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp

TId = TypeVar("TId", bound=EntityId)


class AggregateRoot[TId: EntityId](Entity[TId]):
    """Base class for Aggregate Roots in Domain-Driven Design.

    An Aggregate Root defines a boundary for data consistency and invariants.
    Only Aggregate Roots can be retrieved directly from Repositories.
    """

    def __init__(
        self,
        id: TId,
        created_at: Timestamp | None = None,
        version: int = 0,
    ) -> None:
        """Initialize an AggregateRoot.

        Args:
            id: Unique identifier for the aggregate root.
            created_at: Creation timestamp.
            version: Monotonic version counter for optimistic concurrency control.
        """
        super().__init__(id=id, created_at=created_at)
        self._domain_events: list[DomainEvent] = []
        self._version: int = version

    @property
    def domain_events(self) -> list[DomainEvent]:
        """Read-only view of uncommitted domain events."""
        return list(self._domain_events)

    @property
    def version(self) -> int:
        """Optimistic concurrency version number."""
        return self._version

    def _raise_event(self, event: DomainEvent) -> None:
        """Record a domain event to be published when the Unit of Work commits.

        Args:
            event: The DomainEvent instance capturing state change.
        """
        self._domain_events.append(event)

    def clear_events(self) -> list[DomainEvent]:
        """Flush and return all recorded domain events.

        Returns:
            List of domain events recorded prior to flushing.
        """
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
