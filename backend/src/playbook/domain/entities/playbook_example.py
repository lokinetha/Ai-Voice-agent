"""
PlaybookExample Entity for Playbook Bounded Context.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class PlaybookExample(Entity[EntityId]):
    """Few-shot conversation example entity belonging to a Playbook."""

    def __init__(
        self,
        id: EntityId,
        scenario: str,
        user_input: str,
        ideal_response: str,
        explanation: str = "",
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not scenario or not scenario.strip():
            raise ValueError("PlaybookExample scenario cannot be empty")
        if not user_input or not user_input.strip():
            raise ValueError("PlaybookExample user_input cannot be empty")
        if not ideal_response or not ideal_response.strip():
            raise ValueError("PlaybookExample ideal_response cannot be empty")

        self._scenario = scenario.strip()
        self._user_input = user_input.strip()
        self._ideal_response = ideal_response.strip()
        self._explanation = explanation.strip()

    @property
    def scenario(self) -> str:
        return self._scenario

    @property
    def user_input(self) -> str:
        return self._user_input

    @property
    def ideal_response(self) -> str:
        return self._ideal_response

    @property
    def explanation(self) -> str:
        return self._explanation
