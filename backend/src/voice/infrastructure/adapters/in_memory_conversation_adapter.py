"""
InMemoryConversationAdapter implementing ConversationPort and ConversationContextPort.

Provides an in-memory conversation store for multi-turn local development, testing,
and CLI execution without requiring an active database session.
"""

from __future__ import annotations

from agent_runtime.application.dto.agent_runtime_dto import ConversationTurnDTO
from agent_runtime.application.ports.conversation_context_port import (
    ConversationContextPort,
)

from voice.domain.ports.conversation_port import ConversationPort


class InMemoryConversationStore:
    """Shared in-memory conversation message store."""

    def __init__(self) -> None:
        self.conversations: dict[str, list[dict[str, str]]] = {}

    def append(self, conversation_id: str, role: str, content: str) -> str:
        """Append message turn to in-memory conversation store."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        msg_id = f"msg-{len(self.conversations[conversation_id]) + 1}"
        self.conversations[conversation_id].append({
            "id": msg_id,
            "role": role,
            "content": content,
        })
        return msg_id

    def get_history(self, conversation_id: str) -> list[dict[str, str]]:
        """Get copy of all recorded turns for a conversation."""
        return list(self.conversations.get(conversation_id, []))


class InMemoryConversationAdapter(ConversationPort, ConversationContextPort):
    """Unified in-memory adapter implementing both ConversationPort and ConversationContextPort."""

    def __init__(self, store: InMemoryConversationStore | None = None) -> None:
        self._store = store or InMemoryConversationStore()

    @property
    def store(self) -> InMemoryConversationStore:
        return self._store

    async def append_message_to_conversation(
        self, conversation_id: str, role: str, content: str
    ) -> str:
        """Record turn from Voice context (ConversationPort)."""
        return self._store.append(conversation_id, role, content)

    async def get_conversation_history(
        self, conversation_id: str
    ) -> list[ConversationTurnDTO]:
        """Fetch history for Agent Runtime context (ConversationContextPort)."""
        raw_turns = self._store.get_history(conversation_id)
        return [
            ConversationTurnDTO(
                message_id=t["id"],
                role=t["role"],
                content=t["content"],
            )
            for t in raw_turns
        ]

    async def append_message(
        self, conversation_id: str, role: str, content: str
    ) -> str:
        """Record message from Agent Runtime (ConversationContextPort)."""
        return self._store.append(conversation_id, role, content)
