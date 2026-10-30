"""
ParticipantJoined Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class ParticipantJoined(DomainEvent):
    """Domain Event published when a Participant joins a Conversation."""

    conversation_id: str = ""
    participant_id: str = ""
    role: str = ""
    name: str = ""
