"""
PlaybookTransition Entity for Playbook Bounded Context.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class PlaybookTransition(Entity[EntityId]):
    """Transition rule entity governing movement between Playbook Stages."""

    def __init__(
        self,
        id: EntityId,
        from_stage_id: EntityId,
        to_stage_id: EntityId,
        condition: str = "",
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if from_stage_id is None or to_stage_id is None:
            raise ValueError("from_stage_id and to_stage_id must not be None")
        if from_stage_id == to_stage_id:
            raise ValueError("Transition cannot connect a stage to itself")

        self._from_stage_id = from_stage_id
        self._to_stage_id = to_stage_id
        self._condition = condition.strip()

    @property
    def from_stage_id(self) -> EntityId:
        return self._from_stage_id

    @property
    def to_stage_id(self) -> EntityId:
        return self._to_stage_id

    @property
    def condition(self) -> str:
        return self._condition
