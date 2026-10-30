"""
Participant Entity for Conversation Bounded Context.

Represents a party in a Conversation (Agent, Customer, Supervisor, or System).
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp

from conversation.domain.value_objects.participant_role import ParticipantRole


class Participant(Entity[EntityId]):
    """Participant Entity child of Conversation Aggregate Root."""

    def __init__(
        self,
        id: EntityId,
        name: str,
        role: ParticipantRole,
        external_id: str = "",
        is_active: bool = True,
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not name or not isinstance(name, str) or not name.strip():
            raise ValueError("Participant name cannot be empty")

        self._name = name.strip()
        self._role = role
        self._external_id = external_id
        self._is_active = is_active

    @property
    def name(self) -> str:
        return self._name

    @property
    def role(self) -> ParticipantRole:
        return self._role

    @property
    def external_id(self) -> str:
        return self._external_id

    @property
    def is_active(self) -> bool:
        return self._is_active

    def deactivate(self) -> None:
        """Mark participant as inactive (left the conversation)."""
        self._is_active = False
