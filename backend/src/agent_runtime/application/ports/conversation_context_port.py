"""
ConversationContextPort Interface for Agent Runtime.

Abstract port for loading Conversation history and appending generated agent messages.
Enforces rule: Conversation is the single source of truth for conversational messages.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agent_runtime.application.dto.agent_runtime_dto import ConversationTurnDTO


class ConversationContextPort(ABC):
    """Abstract port interfacing Agent Runtime with Conversation context."""

    @abstractmethod
    async def get_conversation_history(
        self, conversation_id: str
    ) -> list[ConversationTurnDTO]:
        """Fetch past message turns for conversation history context.

        Args:
            conversation_id: Target Conversation ID.

        Returns:
            List of ConversationTurnDTO objects.
        """
        ...

    @abstractmethod
    async def append_message(
        self, conversation_id: str, role: str, content: str
    ) -> str:
        """Record generated turn into target Conversation aggregate.

        Args:
            conversation_id: Target Conversation ID.
            role: Speaker role ("CUSTOMER", "AGENT", etc.).
            content: Text message content.

        Returns:
            Generated message ID string.
        """
        ...
