"""
GetPlaybookVersion Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import PlaybookId

from playbook.application.dto.playbook_dto import PlaybookDTO
from playbook.application.mappers.playbook_mapper import PlaybookMapper
from playbook.domain.repositories.playbook_repository import PlaybookRepository


@dataclass(frozen=True)
class GetPlaybookVersionQuery(Query):
    """Query requesting a specific published Playbook version snapshot."""

    playbook_id: str
    version_number: int


class GetPlaybookVersionHandler(QueryHandler[GetPlaybookVersionQuery, PlaybookDTO]):
    """Handler executing GetPlaybookVersionQuery."""

    def __init__(self, playbook_repository: PlaybookRepository) -> None:
        self._repo = playbook_repository

    async def handle(self, query: GetPlaybookVersionQuery) -> Result[PlaybookDTO]:
        """Execute GetPlaybookVersionQuery."""
        if not query.playbook_id:
            return Result.fail(Error("VALIDATION_ERROR", "Playbook ID cannot be empty"))
        if query.version_number < 1:
            return Result.fail(Error("VALIDATION_ERROR", "Version number must be >= 1"))

        pb = await self._repo.find_published_version(
            PlaybookId(query.playbook_id), query.version_number
        )
        if pb is None:
            return Result.fail(
                Error(
                    "NOT_FOUND",
                    f"Playbook version '{query.version_number}' for '{query.playbook_id}' not found",
                )
            )

        return Result.ok(PlaybookMapper.to_dto(pb))
