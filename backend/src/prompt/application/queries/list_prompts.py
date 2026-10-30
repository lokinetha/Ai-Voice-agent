"""
ListPrompts Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import WorkspaceId

from prompt.application.dto.prompt_dto import PromptDTO
from prompt.application.mappers.prompt_mapper import PromptMapper
from prompt.domain.repositories.prompt_repository import PromptRepository


@dataclass(frozen=True)
class ListPromptsQuery(Query):
    """Query requesting Prompts in a Workspace."""

    workspace_id: str


class ListPromptsHandler(QueryHandler[ListPromptsQuery, tuple[PromptDTO, ...]]):
    """Handler executing ListPromptsQuery."""

    def __init__(self, prompt_repository: PromptRepository) -> None:
        self._repo = prompt_repository

    async def handle(self, query: ListPromptsQuery) -> Result[tuple[PromptDTO, ...]]:
        """Execute ListPromptsQuery."""
        if not query.workspace_id:
            return Result.fail(Error("VALIDATION_ERROR", "Workspace ID cannot be empty"))

        prompts = await self._repo.find_by_workspace(WorkspaceId(query.workspace_id))
        dtos = tuple(PromptMapper.to_dto(p) for p in prompts)
        return Result.ok(dtos)
