"""
PlaybookGoal Entity for Playbook Bounded Context.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class PlaybookGoal(Entity[EntityId]):
    """Goal entity defined within a Playbook or Playbook Stage."""

    def __init__(
        self,
        id: EntityId,
        name: str,
        description: str = "",
        priority: int = 1,
        is_mandatory: bool = True,
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not name or not name.strip():
            raise ValueError("PlaybookGoal name cannot be empty")
        if priority < 1:
            raise ValueError("PlaybookGoal priority must be >= 1")

        self._name = name.strip()
        self._description = description.strip()
        self._priority = priority
        self._is_mandatory = is_mandatory

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def is_mandatory(self) -> bool:
        return self._is_mandatory
