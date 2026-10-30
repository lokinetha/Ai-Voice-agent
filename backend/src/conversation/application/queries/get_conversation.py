"""
GetConversation Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import ConversationId

from conversation.application.dto.conversation_dto import ConversationDTO
from conversation.application.mappers.conversation_mapper import (
    ConversationMapper,
)
from conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)


@dataclass(frozen=True)
class GetConversationQuery(Query):
    """Query requesting Conversation details by ID."""

    conversation_id: str
    include_messages: bool = True
    include_participants: bool = True


class GetConversationHandler(QueryHandler[GetConversationQuery, ConversationDTO]):
    """Handler executing GetConversationQuery."""

    def __init__(self, conv_repository: ConversationRepository) -> None:
        self._conv_repo = conv_repository

    async def handle(self, query: GetConversationQuery) -> Result[ConversationDTO]:
        """Execute GetConversationQuery."""
        if not query.conversation_id:
            return Result.fail(Error("VALIDATION_ERROR", "Conversation ID cannot be empty"))

        conv = await self._conv_repo.get_by_id(ConversationId(query.conversation_id))
        if conv is None:
            return Result.fail(Error("NOT_FOUND", f"Conversation '{query.conversation_id}' not found"))

        return Result.ok(
            ConversationMapper.to_conversation_dto(
                conv,
                include_messages=query.include_messages,
                include_participants=query.include_participants,
            )
        )
