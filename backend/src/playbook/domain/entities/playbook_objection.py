"""
PlaybookObjection Entity for Playbook Bounded Context.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class PlaybookObjection(Entity[EntityId]):
    """Objection handling entity describing user objections and resolution strategy."""

    def __init__(
        self,
        id: EntityId,
        trigger_phrase: str,
        objection_category: str,
        response_strategy: str,
        recommended_response: str = "",
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not trigger_phrase or not trigger_phrase.strip():
            raise ValueError("PlaybookObjection trigger_phrase cannot be empty")
        if not response_strategy or not response_strategy.strip():
            raise ValueError("PlaybookObjection response_strategy cannot be empty")

        self._trigger_phrase = trigger_phrase.strip()
        self._objection_category = objection_category.strip() or "GENERAL"
        self._response_strategy = response_strategy.strip()
        self._recommended_response = recommended_response.strip()

    @property
    def trigger_phrase(self) -> str:
        return self._trigger_phrase

    @property
    def objection_category(self) -> str:
        return self._objection_category

    @property
    def response_strategy(self) -> str:
        return self._response_strategy

    @property
    def recommended_response(self) -> str:
        return self._recommended_response
