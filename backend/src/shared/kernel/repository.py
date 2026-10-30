"""
Repository Base Interface.

Defines generic data access abstraction for Aggregate Roots in the Domain layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from shared.kernel.aggregate_root import AggregateRoot
from shared.kernel.specification import Specification
from shared.kernel.value_objects import EntityId

T = TypeVar("T", bound=AggregateRoot)
TId = TypeVar("TId", bound=EntityId)


class Repository[T: AggregateRoot, TId: EntityId](ABC):
    """Generic Repository Interface.

    Operates solely on Aggregate Roots to preserve encapsulation and aggregate consistency boundaries.
    """

    @abstractmethod
    async def get_by_id(self, id: TId) -> T | None:
        """Retrieve an aggregate root by its typed identifier.

        Args:
            id: Typed EntityId instance.

        Returns:
            The AggregateRoot instance if found, or None.
        """
        ...

    @abstractmethod
    async def save(self, aggregate: T) -> None:
        """Persist or update an aggregate root.

        Args:
            aggregate: AggregateRoot instance to save.
        """
        ...

    @abstractmethod
    async def delete(self, aggregate: T) -> None:
        """Remove an aggregate root from persistence.

        Args:
            aggregate: AggregateRoot instance to delete.
        """
        ...

    @abstractmethod
    async def find(self, spec: Specification[T]) -> list[T]:
        """Find aggregate roots satisfying a specification.

        Args:
            spec: Specification predicate.

        Returns:
            List of matching AggregateRoot instances.
        """
        ...

    @abstractmethod
    async def count(self, spec: Specification[T]) -> int:
        """Count aggregate roots satisfying a specification.

        Args:
            spec: Specification predicate.

        Returns:
            Total count of matching aggregates.
        """
        ...
