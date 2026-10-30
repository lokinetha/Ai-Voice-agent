"""
ListProcessingJobs Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import WorkspaceId

from processing.application.dto.processing_dto import ProcessingJobDTO
from processing.application.mappers.processing_job_mapper import (
    ProcessingJobMapper,
)
from processing.domain.repositories.processing_job_repository import (
    ProcessingJobRepository,
)


@dataclass(frozen=True)
class ListProcessingJobsQuery(Query):
    """Query requesting ProcessingJobs in a Workspace."""

    workspace_id: str


class ListProcessingJobsHandler(QueryHandler[ListProcessingJobsQuery, tuple[ProcessingJobDTO, ...]]):
    """Handler executing ListProcessingJobsQuery."""

    def __init__(self, job_repository: ProcessingJobRepository) -> None:
        self._repo = job_repository

    async def handle(self, query: ListProcessingJobsQuery) -> Result[tuple[ProcessingJobDTO, ...]]:
        """Execute ListProcessingJobsQuery."""
        if not query.workspace_id:
            return Result.fail(Error("VALIDATION_ERROR", "Workspace ID cannot be empty"))

        jobs = await self._repo.find_by_workspace(WorkspaceId(query.workspace_id))
        dtos = tuple(ProcessingJobMapper.to_dto(j) for j in jobs)
        return Result.ok(dtos)
