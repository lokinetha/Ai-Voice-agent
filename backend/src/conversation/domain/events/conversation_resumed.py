"""
ConversationResumed Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class ConversationResumed(DomainEvent):
    """Domain Event published when a paused Conversation is resumed."""

    conversation_id: str = ""
