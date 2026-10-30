"""
ConversationPort Interface for Voice Bounded Context.

Abstract port for recording voice-session turns into the Conversation aggregate.
Enforces rule: Conversation is the source of truth for conversational messages.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ConversationPort(ABC):
    """Abstract application port interfacing Voice bounded context with Conversation."""

    @abstractmethod
    async def append_message_to_conversation(
        self, conversation_id: str, role: str, content: str
    ) -> str:
        """Record transcribed or generated turn into target Conversation aggregate.

        Args:
            conversation_id: Target Conversation ID.
            role: Speaker role (e.g. "CUSTOMER", "AGENT").
            content: Text message content.

        Returns:
            Generated message ID string.
        """
        ...
