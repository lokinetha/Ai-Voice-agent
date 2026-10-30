"""
Workspace Entity for Organization Bounded Context.

Represents an isolated environment (workspace) owned by an Organization.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.result import Result
from shared.kernel.value_objects import Timestamp, WorkspaceId


class Workspace(Entity[WorkspaceId]):
    """Workspace Entity child of Organization aggregate root.

    Attributes:
        name: Human readable workspace name string.
        status: Status string ('active', 'deactivated').
    """

    def __init__(
        self,
        id: WorkspaceId,
        name: str,
        status: str = "active",
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not name or not isinstance(name, str) or not name.strip():
            raise ValueError("Workspace name cannot be empty")

        self._name = name.strip()
        self._status = status

    @property
    def name(self) -> str:
        """Get workspace name."""
        return self._name

    @property
    def status(self) -> str:
        """Get workspace status string."""
        return self._status

    @property
    def is_active(self) -> bool:
        """Check if workspace is active."""
        return self._status == "active"

    def activate(self) -> Result[None]:
        """Activate workspace."""
        if self._status == "active":
            return Result.ok(None)
        self._status = "active"
        return Result.ok(None)

    def deactivate(self) -> Result[None]:
        """Deactivate workspace."""
        if self._status == "deactivated":
            return Result.ok(None)
        self._status = "deactivated"
        return Result.ok(None)
