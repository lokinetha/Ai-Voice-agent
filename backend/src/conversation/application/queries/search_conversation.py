"""
SearchConversation Query and QueryHandler.

Performs metadata-level filtering over conversations (status, agent).
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import AgentId

from conversation.application.dto.conversation_dto import ConversationDTO
from conversation.application.mappers.conversation_mapper import (
    ConversationMapper,
)
from conversation.domain.entities.conversation import Conversation
from conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)


@dataclass(frozen=True)
class SearchConversationQuery(Query):
    """Query filtering Conversations by agent_id or status."""

    agent_id: str | None = None
    status: str | None = None


class SearchConversationHandler(QueryHandler[SearchConversationQuery, tuple[ConversationDTO, ...]]):
    """Handler executing SearchConversationQuery."""

    def __init__(self, conv_repository: ConversationRepository) -> None:
        self._conv_repo = conv_repository

    async def handle(self, query: SearchConversationQuery) -> Result[tuple[ConversationDTO, ...]]:
        """Execute SearchConversationQuery."""
        if not query.agent_id and not query.status:
            return Result.fail(Error("VALIDATION_ERROR", "At least one filter parameter required"))

        convs: list[Conversation] = []
        if query.agent_id:
            convs = await self._conv_repo.find_by_agent(AgentId(query.agent_id))
        else:
            from conversation.domain.specifications.active_conversation_spec import (
                ActiveConversationSpec,
            )

            convs = await self._conv_repo.find(ActiveConversationSpec())

        # Apply status filter if provided
        if query.status:
            status_upper = query.status.upper()
            convs = [c for c in convs if c.status.value.value == status_upper]

        dtos = tuple(ConversationMapper.to_conversation_dto(c) for c in convs)
        return Result.ok(dtos)
