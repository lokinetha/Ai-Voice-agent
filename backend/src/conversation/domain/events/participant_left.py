"""
ParticipantLeft Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class ParticipantLeft(DomainEvent):
    """Domain Event published when a Participant leaves a Conversation."""

    conversation_id: str = ""
    participant_id: str = ""
    role: str = ""
