"""
GetConversationMessages Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import ConversationId

from conversation.application.dto.conversation_dto import MessageDTO
from conversation.application.mappers.conversation_mapper import (
    ConversationMapper,
)
from conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)


@dataclass(frozen=True)
class GetConversationMessagesQuery(Query):
    """Query requesting Messages for a Conversation."""

    conversation_id: str


class GetConversationMessagesHandler(QueryHandler[GetConversationMessagesQuery, tuple[MessageDTO, ...]]):
    """Handler executing GetConversationMessagesQuery."""

    def __init__(self, conv_repository: ConversationRepository) -> None:
        self._conv_repo = conv_repository

    async def handle(self, query: GetConversationMessagesQuery) -> Result[tuple[MessageDTO, ...]]:
        """Execute GetConversationMessagesQuery."""
        if not query.conversation_id:
            return Result.fail(Error("VALIDATION_ERROR", "Conversation ID cannot be empty"))

        conv = await self._conv_repo.get_by_id(ConversationId(query.conversation_id))
        if conv is None:
            return Result.fail(Error("NOT_FOUND", f"Conversation '{query.conversation_id}' not found"))

        dtos = tuple(ConversationMapper.to_message_dto(m) for m in conv.messages)
        return Result.ok(dtos)
