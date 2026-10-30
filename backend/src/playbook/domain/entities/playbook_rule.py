"""
PlaybookRule Entity for Playbook Bounded Context.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class PlaybookRule(Entity[EntityId]):
    """Behavioral rule entity enforcing specific agent constraints."""

    def __init__(
        self,
        id: EntityId,
        name: str,
        condition: str,
        action: str,
        is_strict: bool = True,
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not name or not name.strip():
            raise ValueError("PlaybookRule name cannot be empty")
        if not action or not action.strip():
            raise ValueError("PlaybookRule action cannot be empty")

        self._name = name.strip()
        self._condition = condition.strip()
        self._action = action.strip()
        self._is_strict = is_strict

    @property
    def name(self) -> str:
        return self._name

    @property
    def condition(self) -> str:
        return self._condition

    @property
    def action(self) -> str:
        return self._action

    @property
    def is_strict(self) -> bool:
        return self._is_strict
