"""
ConversationMapper for mapping between Domain and Application DTOs.
"""

from __future__ import annotations

from conversation.application.dto.conversation_dto import (
    ConversationDTO,
    ConversationMetricsDTO,
    ConversationSummaryDTO,
    MessageDTO,
    ParticipantDTO,
)
from conversation.domain.entities.conversation import Conversation
from conversation.domain.entities.message import Message
from conversation.domain.entities.participant import Participant


class ConversationMapper:
    """Static mapper for Conversation domain ↔ DTO conversion."""

    @staticmethod
    def to_conversation_dto(
        conv: Conversation,
        include_messages: bool = False,
        include_participants: bool = False,
    ) -> ConversationDTO:
        """Map Conversation aggregate root to ConversationDTO."""
        metrics_dto = ConversationMetricsDTO(
            duration_seconds=conv.metrics.duration_seconds,
            total_messages=conv.metrics.total_messages,
            agent_messages=conv.metrics.agent_messages,
            customer_messages=conv.metrics.customer_messages,
            turn_count=conv.metrics.turn_count,
        )

        summary_dto = None
        if conv.summary is not None:
            summary_dto = ConversationSummaryDTO(
                text=conv.summary.text,
                key_topics=conv.summary.key_topics,
                sentiment=conv.summary.sentiment,
                action_items=conv.summary.action_items,
            )

        participants = (
            tuple(ConversationMapper.to_participant_dto(p) for p in conv.participants)
            if include_participants
            else ()
        )

        messages = (
            tuple(ConversationMapper.to_message_dto(m) for m in conv.messages)
            if include_messages
            else ()
        )

        return ConversationDTO(
            id=str(conv.id.value),
            workspace_id=str(conv.workspace_id.value),
            agent_id=str(conv.agent_id.value),
            channel=conv.channel.value.value,
            language=conv.language.code,
            status=conv.status.value.value,
            message_count=conv.message_count,
            participant_count=conv.participant_count,
            version=conv.version,
            created_at=conv.created_at.value,
            metrics=metrics_dto,
            summary=summary_dto,
            participants=participants,
            messages=messages,
        )

    @staticmethod
    def to_message_dto(msg: Message) -> MessageDTO:
        """Map Message entity to MessageDTO."""
        return MessageDTO(
            id=str(msg.id.value),
            participant_id=str(msg.participant_id.value),
            participant_role=msg.role.value.value,
            content=msg.content,
            sequence_number=msg.sequence_number,
            metadata=msg.metadata,
            created_at=msg.created_at.value,
        )

    @staticmethod
    def to_participant_dto(p: Participant) -> ParticipantDTO:
        """Map Participant entity to ParticipantDTO."""
        return ParticipantDTO(
            id=str(p.id.value),
            name=p.name,
            role=p.role.value.value,
            external_id=p.external_id,
            is_active=p.is_active,
            created_at=p.created_at.value,
        )
