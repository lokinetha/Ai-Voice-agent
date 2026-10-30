"""
TranscriptAdapter implementing TranscriptProviderPort.
"""

from __future__ import annotations

from typing import Any

from conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from processing.domain.ports.transcript_provider_port import (
    TranscriptProviderPort,
)
from shared.kernel.value_objects import ConversationId


class TranscriptAdapter(TranscriptProviderPort):
    """Adapter supplying structured message turns for analysis."""

    def __init__(self, conversation_repository: ConversationRepository) -> None:
        self._conv_repo = conversation_repository

    async def get_transcript_messages(
        self, conversation_id: str
    ) -> list[dict[str, Any]]:
        """Fetch structured transcript message turns.

        Args:
            conversation_id: Target Conversation ID.

        Returns:
            List of message dictionaries.
        """
        conv = await self._conv_repo.get_by_id(ConversationId(conversation_id))
        if conv is None:
            return []

        return [
            {
                "id": str(m.id.value),
                "participant_id": str(m.participant_id.value),
                "role": m.role.value.value,
                "content": m.content,
                "sequence_number": m.sequence_number,
            }
            for m in conv.messages
        ]
