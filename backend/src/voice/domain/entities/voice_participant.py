"""
VoiceParticipant Entity for Voice Bounded Context.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class VoiceParticipant(Entity[EntityId]):
    """Entity representing a participant in a real-time VoiceSession (e.g. USER, AGENT)."""

    def __init__(
        self,
        id: EntityId,
        role: str,
        display_name: str = "",
        phone_number: str = "",
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not role or not role.strip():
            raise ValueError("VoiceParticipant role cannot be empty")

        self._role = role.strip().upper()
        self._display_name = display_name.strip()
        self._phone_number = phone_number.strip()

    @property
    def role(self) -> str:
        return self._role

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def phone_number(self) -> str:
        return self._phone_number
