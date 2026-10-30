"""
ListPlaybooks Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import WorkspaceId

from playbook.application.dto.playbook_dto import PlaybookDTO
from playbook.application.mappers.playbook_mapper import PlaybookMapper
from playbook.domain.repositories.playbook_repository import PlaybookRepository


@dataclass(frozen=True)
class ListPlaybooksQuery(Query):
    """Query requesting Playbooks in a Workspace."""

    workspace_id: str


class ListPlaybooksHandler(QueryHandler[ListPlaybooksQuery, tuple[PlaybookDTO, ...]]):
    """Handler executing ListPlaybooksQuery."""

    def __init__(self, playbook_repository: PlaybookRepository) -> None:
        self._repo = playbook_repository

    async def handle(self, query: ListPlaybooksQuery) -> Result[tuple[PlaybookDTO, ...]]:
        """Execute ListPlaybooksQuery."""
        if not query.workspace_id:
            return Result.fail(Error("VALIDATION_ERROR", "Workspace ID cannot be empty"))

        playbooks = await self._repo.find_by_workspace(WorkspaceId(query.workspace_id))
        dtos = tuple(PlaybookMapper.to_dto(pb) for pb in playbooks)
        return Result.ok(dtos)
