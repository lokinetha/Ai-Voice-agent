"""
GetConversationAnalysis Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import EntityId

from processing.application.dto.conversation_analysis_dto import (
    ConversationAnalysisDTO,
)
from processing.application.mappers.conversation_analysis_mapper import (
    ConversationAnalysisMapper,
)
from processing.domain.repositories.conversation_analysis_repository import (
    ConversationAnalysisRepository,
)


@dataclass(frozen=True)
class GetConversationAnalysisQuery(Query):
    """Query requesting ConversationAnalysis details by ID."""

    analysis_id: str


class GetConversationAnalysisHandler(QueryHandler[GetConversationAnalysisQuery, ConversationAnalysisDTO]):
    """Handler executing GetConversationAnalysisQuery."""

    def __init__(self, analysis_repository: ConversationAnalysisRepository) -> None:
        self._repo = analysis_repository

    async def handle(self, query: GetConversationAnalysisQuery) -> Result[ConversationAnalysisDTO]:
        """Execute GetConversationAnalysisQuery."""
        if not query.analysis_id:
            return Result.fail(Error("VALIDATION_ERROR", "Analysis ID cannot be empty"))

        analysis = await self._repo.get_by_id(EntityId(query.analysis_id))
        if analysis is None:
            return Result.fail(Error("NOT_FOUND", f"ConversationAnalysis '{query.analysis_id}' not found"))

        return Result.ok(ConversationAnalysisMapper.to_dto(analysis))
