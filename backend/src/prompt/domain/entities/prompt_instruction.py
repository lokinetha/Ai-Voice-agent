"""
PromptInstruction Entity for Prompt Bounded Context.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class PromptInstruction(Entity[EntityId]):
    """Specific instruction line within a Prompt Section."""

    def __init__(
        self,
        id: EntityId,
        text: str,
        order: int = 1,
        is_mandatory: bool = True,
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not text or not text.strip():
            raise ValueError("PromptInstruction text cannot be empty")
        if order < 1:
            raise ValueError("PromptInstruction order must be >= 1")

        self._text = text.strip()
        self._order = order
        self._is_mandatory = is_mandatory

    @property
    def text(self) -> str:
        return self._text

    @property
    def order(self) -> int:
        return self._order

    @property
    def is_mandatory(self) -> bool:
        return self._is_mandatory
