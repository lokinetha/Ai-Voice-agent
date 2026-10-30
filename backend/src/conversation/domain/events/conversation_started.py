"""
ConversationStarted Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class ConversationStarted(DomainEvent):
    """Domain Event published when a Conversation is initialized."""

    conversation_id: str = ""
    workspace_id: str = ""
    agent_id: str = ""
    channel: str = ""
