"""
ConversationReaderAdapter implementing ConversationReaderPort.

Adapts the ConversationRepository interface from the Conversation bounded context
to supply read-only ConversationAnalysisDataDTO data.
"""

from __future__ import annotations

from conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from processing.domain.ports.conversation_reader_port import (
    ConversationAnalysisDataDTO,
    ConversationMessageData,
    ConversationReaderPort,
)
from shared.kernel.value_objects import ConversationId


class ConversationReaderAdapter(ConversationReaderPort):
    """Adapter reading completed conversation details."""

    def __init__(self, conversation_repository: ConversationRepository) -> None:
        self._conv_repo = conversation_repository

    async def get_completed_conversation(
        self, conversation_id: str
    ) -> ConversationAnalysisDataDTO | None:
        """Fetch completed conversation and return read-only DTO.

        Args:
            conversation_id: Target Conversation ID.

        Returns:
            ConversationAnalysisDataDTO if found, else None.
        """
        conv = await self._conv_repo.get_by_id(ConversationId(conversation_id))
        if conv is None:
            return None

        msg_data = tuple(
            ConversationMessageData(
                id=str(m.id.value),
                participant_id=str(m.participant_id.value),
                role=m.role.value.value,
                content=m.content,
                sequence_number=m.sequence_number,
            )
            for m in conv.messages
        )

        return ConversationAnalysisDataDTO(
            conversation_id=str(conv.id.value),
            workspace_id=str(conv.workspace_id.value),
            agent_id=str(conv.agent_id.value),
            status=conv.status.value.value,
            messages=msg_data,
        )
