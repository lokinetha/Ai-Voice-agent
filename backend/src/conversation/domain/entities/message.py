"""
Message Entity for Conversation Bounded Context.

Represents a single immutable message exchanged within a Conversation.
Messages are append-only and cannot be modified after creation.
"""

from __future__ import annotations

from typing import Any

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, MessageId, Timestamp

from conversation.domain.value_objects.participant_role import ParticipantRole


class Message(Entity[MessageId]):
    """Message Entity child of Conversation Aggregate Root.

    Once created, a Message is immutable — no setters are exposed.
    """

    def __init__(
        self,
        id: MessageId,
        participant_id: EntityId,
        role: ParticipantRole,
        content: str,
        sequence_number: int,
        metadata: dict[str, Any] | None = None,
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not content or not isinstance(content, str):
            raise ValueError("Message content cannot be empty")
        if sequence_number < 0:
            raise ValueError("sequence_number cannot be negative")

        self._participant_id = participant_id
        self._role = role
        self._content = content
        self._sequence_number = sequence_number
        self._metadata: dict[str, Any] = dict(metadata) if metadata else {}

    @property
    def participant_id(self) -> EntityId:
        return self._participant_id

    @property
    def role(self) -> ParticipantRole:
        return self._role

    @property
    def content(self) -> str:
        return self._content

    @property
    def sequence_number(self) -> int:
        return self._sequence_number

    @property
    def metadata(self) -> dict[str, Any]:
        return dict(self._metadata)
