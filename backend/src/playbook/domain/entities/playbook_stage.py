"""
PlaybookStage Entity for Playbook Bounded Context.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp

from playbook.domain.entities.playbook_goal import PlaybookGoal


class PlaybookStage(Entity[EntityId]):
    """Conversation stage entity organizing goals and flow within a Playbook."""

    def __init__(
        self,
        id: EntityId,
        name: str,
        order: int = 1,
        description: str = "",
        goals: Sequence[PlaybookGoal] = (),
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not name or not name.strip():
            raise ValueError("PlaybookStage name cannot be empty")
        if order < 1:
            raise ValueError("PlaybookStage order must be >= 1")

        self._name = name.strip()
        self._order = order
        self._description = description.strip()
        self._goals: list[PlaybookGoal] = list(goals)

    @property
    def name(self) -> str:
        return self._name

    @property
    def order(self) -> int:
        return self._order

    @property
    def description(self) -> str:
        return self._description

    @property
    def goals(self) -> tuple[PlaybookGoal, ...]:
        return tuple(self._goals)

    def add_goal(self, goal: PlaybookGoal) -> None:
        """Add a goal to this stage."""
        self._goals.append(goal)
