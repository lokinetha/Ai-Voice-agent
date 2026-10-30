"""
AggregateBehaviorPatterns Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
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
class AggregateBehaviorPatternsCommand(Command):
    """Command requesting workspace-wide behavior pattern aggregation."""

    workspace_id: str


class AggregateBehaviorPatternsHandler(CommandHandler[AggregateBehaviorPatternsCommand, tuple[ConversationPatternDTO, ...]]):
    """Handler executing AggregateBehaviorPatternsCommand across completed workspace analyses."""

    def __init__(self, analysis_repository: ConversationAnalysisRepository) -> None:
        self._repo = analysis_repository

    async def handle(self, command: AggregateBehaviorPatternsCommand) -> Result[tuple[ConversationPatternDTO, ...]]:
        """Execute workspace pattern aggregation."""
        if not command.workspace_id:
            return Result.fail(Error("VALIDATION_ERROR", "Workspace ID cannot be empty"))

        analyses = await self._repo.find_by_workspace(WorkspaceId(command.workspace_id))
        all_patterns: list[ConversationPattern] = []
        for a in analyses:
            all_patterns.extend(a.patterns)

        pat_dtos = tuple(ConversationAnalysisMapper.to_pattern_dto(p) for p in all_patterns)
        return Result.ok(pat_dtos)
