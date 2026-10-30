"""
GetPromptVersion Query and QueryHandler.
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
class GetPromptVersionQuery(Query):
    """Query requesting a specific published Prompt version snapshot."""

    prompt_id: str
    version_number: int


class GetPromptVersionHandler(QueryHandler[GetPromptVersionQuery, PromptDTO]):
    """Handler executing GetPromptVersionQuery."""

    def __init__(self, prompt_repository: PromptRepository) -> None:
        self._repo = prompt_repository

    async def handle(self, query: GetPromptVersionQuery) -> Result[PromptDTO]:
        """Execute GetPromptVersionQuery."""
        if not query.prompt_id:
            return Result.fail(Error("VALIDATION_ERROR", "Prompt ID cannot be empty"))
        if query.version_number < 1:
            return Result.fail(Error("VALIDATION_ERROR", "Version number must be >= 1"))

        prompt = await self._repo.find_published_version(
            PromptId(query.prompt_id), query.version_number
        )
        if prompt is None:
            return Result.fail(
                Error(
                    "NOT_FOUND",
                    f"Prompt version '{query.version_number}' for '{query.prompt_id}' not found",
                )
            )

        return Result.ok(PromptMapper.to_dto(prompt))
