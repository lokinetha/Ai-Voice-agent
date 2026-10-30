"""
MessageAdded Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class MessageAdded(DomainEvent):
    """Domain Event published when a Message is appended to a Conversation."""

    conversation_id: str = ""
    message_id: str = ""
    participant_id: str = ""
    participant_role: str = ""
    sequence_number: int = 0
