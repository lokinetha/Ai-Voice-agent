"""
PromptExample Entity for Prompt Bounded Context.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class PromptExample(Entity[EntityId]):
    """Few-shot conversation turn example inside a Prompt."""

    def __init__(
        self,
        id: EntityId,
        user_input: str,
        ideal_response: str,
        context: str = "",
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not user_input or not user_input.strip():
            raise ValueError("PromptExample user_input cannot be empty")
        if not ideal_response or not ideal_response.strip():
            raise ValueError("PromptExample ideal_response cannot be empty")

        self._user_input = user_input.strip()
        self._ideal_response = ideal_response.strip()
        self._context = context.strip()

    @property
    def user_input(self) -> str:
        return self._user_input

    @property
    def ideal_response(self) -> str:
        return self._ideal_response

    @property
    def context(self) -> str:
        return self._context
