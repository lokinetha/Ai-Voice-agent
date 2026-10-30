"""
GetPrompt Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import PromptId

from prompt.application.dto.prompt_dto import PromptDTO
from prompt.application.mappers.prompt_mapper import PromptMapper
from prompt.domain.repositories.prompt_repository import PromptRepository


@dataclass(frozen=True)
class GetPromptQuery(Query):
    """Query requesting Prompt details by ID."""

    prompt_id: str


class GetPromptHandler(QueryHandler[GetPromptQuery, PromptDTO]):
    """Handler executing GetPromptQuery."""

    def __init__(self, prompt_repository: PromptRepository) -> None:
        self._repo = prompt_repository

    async def handle(self, query: GetPromptQuery) -> Result[PromptDTO]:
        """Execute GetPromptQuery."""
        if not query.prompt_id:
            return Result.fail(Error("VALIDATION_ERROR", "Prompt ID cannot be empty"))

        prompt = await self._repo.get_by_id(PromptId(query.prompt_id))
        if prompt is None:
            return Result.fail(Error("NOT_FOUND", f"Prompt '{query.prompt_id}' not found"))

        return Result.ok(PromptMapper.to_dto(prompt))
