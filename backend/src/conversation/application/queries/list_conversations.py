"""
ListConversations Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import WorkspaceId

from conversation.application.dto.conversation_dto import ConversationDTO
from conversation.application.mappers.conversation_mapper import (
    ConversationMapper,
)
from conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)


@dataclass(frozen=True)
class ListConversationsQuery(Query):
    """Query requesting Conversations list for a Workspace."""

    workspace_id: str


class ListConversationsHandler(QueryHandler[ListConversationsQuery, tuple[ConversationDTO, ...]]):
    """Handler executing ListConversationsQuery."""

    def __init__(self, conv_repository: ConversationRepository) -> None:
        self._conv_repo = conv_repository

    async def handle(self, query: ListConversationsQuery) -> Result[tuple[ConversationDTO, ...]]:
        """Execute ListConversationsQuery."""
        if not query.workspace_id:
            return Result.fail(Error("VALIDATION_ERROR", "Workspace ID cannot be empty"))

        convs = await self._conv_repo.find_by_workspace(WorkspaceId(query.workspace_id))
        dtos = tuple(ConversationMapper.to_conversation_dto(c) for c in convs)
        return Result.ok(dtos)
