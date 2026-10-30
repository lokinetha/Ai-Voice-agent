"""
ConversationSummarized Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class ConversationSummarized(DomainEvent):
    """Domain Event published when a Conversation summary is recorded."""

    conversation_id: str = ""
    summary_text: str = ""
