"""
UnitOfWork Abstraction Interface.

Manages atomic database transactions and collects uncommitted domain events.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType

from shared.kernel.domain_event import DomainEvent


class UnitOfWork(ABC):
    """Abstract Base Class for the Unit of Work pattern.

    Ensures that transactional operations across multiple repositories and aggregates
    either all succeed or all rollback. Collects domain events to publish post-commit.
    """

    @abstractmethod
    async def __aenter__(self) -> UnitOfWork:
        """Begin context manager scope."""
        ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager scope, performing automatic rollback if an exception occurred."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current active database transaction."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back all changes in the current transaction."""
        ...

    @abstractmethod
    def collect_events(self) -> list[DomainEvent]:
        """Collect uncommitted domain events from tracked aggregates and flush their queues."""
        ...
