"""
ConversationEnded Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class ConversationEnded(DomainEvent):
    """Domain Event published when a Conversation is ended."""

    conversation_id: str = ""
    reason: str = ""
    total_messages: int = 0
