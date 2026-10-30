"""
GetProcessingJob Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import EntityId

from processing.application.dto.processing_dto import ProcessingJobDTO
from processing.application.mappers.processing_job_mapper import (
    ProcessingJobMapper,
)
from processing.domain.repositories.processing_job_repository import (
    ProcessingJobRepository,
)


@dataclass(frozen=True)
class GetProcessingJobQuery(Query):
    """Query requesting ProcessingJob details by ID."""

    job_id: str


class GetProcessingJobHandler(QueryHandler[GetProcessingJobQuery, ProcessingJobDTO]):
    """Handler executing GetProcessingJobQuery."""

    def __init__(self, job_repository: ProcessingJobRepository) -> None:
        self._repo = job_repository

    async def handle(self, query: GetProcessingJobQuery) -> Result[ProcessingJobDTO]:
        """Execute GetProcessingJobQuery."""
        if not query.job_id:
            return Result.fail(Error("VALIDATION_ERROR", "Job ID cannot be empty"))

        job = await self._repo.get_by_id(EntityId(query.job_id))
        if job is None:
            return Result.fail(Error("NOT_FOUND", f"ProcessingJob '{query.job_id}' not found"))

        return Result.ok(ProcessingJobMapper.to_dto(job))
