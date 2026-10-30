"""
PromptSection Entity for Prompt Bounded Context.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp

from prompt.domain.entities.prompt_instruction import PromptInstruction
from prompt.domain.value_objects.prompt_section_type import PromptSectionType


class PromptSection(Entity[EntityId]):
    """Section containing text content and structured instructions within a Prompt."""

    def __init__(
        self,
        id: EntityId,
        section_type: PromptSectionType,
        title: str,
        content: str = "",
        order: int = 1,
        instructions: Sequence[PromptInstruction] = (),
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not title or not title.strip():
            raise ValueError("PromptSection title cannot be empty")
        if order < 1:
            raise ValueError("PromptSection order must be >= 1")

        self._section_type = section_type
        self._title = title.strip()
        self._content = content.strip()
        self._order = order
        self._instructions: list[PromptInstruction] = list(instructions)

    @property
    def section_type(self) -> PromptSectionType:
        return self._section_type

    @property
    def title(self) -> str:
        return self._title

    @property
    def content(self) -> str:
        return self._content

    @property
    def order(self) -> int:
        return self._order

    @property
    def instructions(self) -> tuple[PromptInstruction, ...]:
        return tuple(self._instructions)

    def add_instruction(self, instruction: PromptInstruction) -> None:
        """Add an instruction line to this section."""
        self._instructions.append(instruction)
