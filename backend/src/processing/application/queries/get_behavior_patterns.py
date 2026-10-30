"""
GetBehaviorPatterns Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import WorkspaceId

from processing.application.dto.conversation_analysis_dto import (
    ConversationPatternDTO,
)
from processing.application.mappers.conversation_analysis_mapper import (
    ConversationAnalysisMapper,
)
from processing.domain.entities.conversation_pattern import ConversationPattern
from processing.domain.repositories.conversation_analysis_repository import (
    ConversationAnalysisRepository,
)


@dataclass(frozen=True)
class GetBehaviorPatternsQuery(Query):
    """Query requesting behavior patterns for a workspace."""

    workspace_id: str


class GetBehaviorPatternsHandler(QueryHandler[GetBehaviorPatternsQuery, tuple[ConversationPatternDTO, ...]]):
    """Handler executing GetBehaviorPatternsQuery."""

    def __init__(self, analysis_repository: ConversationAnalysisRepository) -> None:
        self._repo = analysis_repository

    async def handle(self, query: GetBehaviorPatternsQuery) -> Result[tuple[ConversationPatternDTO, ...]]:
        """Execute GetBehaviorPatternsQuery."""
        if not query.workspace_id:
            return Result.fail(Error("VALIDATION_ERROR", "Workspace ID cannot be empty"))

        analyses = await self._repo.find_by_workspace(WorkspaceId(query.workspace_id))
        patterns: list[ConversationPattern] = []
        for a in analyses:
            patterns.extend(a.patterns)

        pat_dtos = tuple(ConversationAnalysisMapper.to_pattern_dto(p) for p in patterns)
        return Result.ok(pat_dtos)
