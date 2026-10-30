"""
FakeConversationContextAdapter implementing ConversationContextPort.

In-memory test double for fetching conversation history and recording generated messages.
"""

from __future__ import annotations

from agent_runtime.application.dto.agent_runtime_dto import ConversationTurnDTO
from agent_runtime.application.ports.conversation_context_port import (
    ConversationContextPort,
)


class FakeConversationContextAdapter(ConversationContextPort):
    """In-memory test double for ConversationContextPort."""

    def __init__(self) -> None:
        self.conversations: dict[str, list[ConversationTurnDTO]] = {}

    def seed_history(self, conversation_id: str, history: list[ConversationTurnDTO]) -> None:
        """Seed initial conversation turns for testing."""
        self.conversations[conversation_id] = list(history)

    async def get_conversation_history(
        self, conversation_id: str
    ) -> list[ConversationTurnDTO]:
        """Return history turns for given conversation."""
        return self.conversations.get(conversation_id, [])

    async def append_message(
        self, conversation_id: str, role: str, content: str
    ) -> str:
        """Append message to conversation history in memory."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        msg_id = f"msg-{len(self.conversations[conversation_id]) + 1}"
        turn = ConversationTurnDTO(message_id=msg_id, role=role, content=content)
        self.conversations[conversation_id].append(turn)
        return msg_id
