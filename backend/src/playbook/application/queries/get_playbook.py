"""
GetPlaybook Query and QueryHandler.
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
class GetPlaybookQuery(Query):
    """Query requesting Playbook details by ID."""

    playbook_id: str


class GetPlaybookHandler(QueryHandler[GetPlaybookQuery, PlaybookDTO]):
    """Handler executing GetPlaybookQuery."""

    def __init__(self, playbook_repository: PlaybookRepository) -> None:
        self._repo = playbook_repository

    async def handle(self, query: GetPlaybookQuery) -> Result[PlaybookDTO]:
        """Execute GetPlaybookQuery."""
        if not query.playbook_id:
            return Result.fail(Error("VALIDATION_ERROR", "Playbook ID cannot be empty"))

        pb = await self._repo.get_by_id(PlaybookId(query.playbook_id))
        if pb is None:
            return Result.fail(Error("NOT_FOUND", f"Playbook '{query.playbook_id}' not found"))

        return Result.ok(PlaybookMapper.to_dto(pb))
