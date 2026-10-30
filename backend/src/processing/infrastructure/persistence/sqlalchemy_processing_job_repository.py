"""
SQLAlchemy 2.x Repository Implementation for ProcessingJob Aggregate Root.
"""

from __future__ import annotations

from datetime import UTC

from processing.domain.entities.processing_job import ProcessingJob
from processing.domain.entities.processing_task import ProcessingTask
from processing.domain.repositories.processing_job_repository import (
    ProcessingJobRepository,
)
from processing.domain.value_objects.chunking_strategy import ChunkingStrategy
from processing.domain.value_objects.embedding_strategy import EmbeddingStrategy
from processing.domain.value_objects.processing_job_status import (
    ProcessingJobStatus,
    ProcessingJobStatusType,
)
from processing.domain.value_objects.processing_result import ProcessingResult
from processing.domain.value_objects.processing_task_type import (
    ProcessingTaskType,
    TaskCategory,
)
from processing.infrastructure.persistence.models import (
    ProcessingJobModel,
    ProcessingTaskModel,
)
from shared.kernel.specification import Specification
from shared.kernel.value_objects import (
    DocumentId,
    EntityId,
    Timestamp,
    WorkspaceId,
)
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyProcessingJobRepository(ProcessingJobRepository):
    """SQLAlchemy implementation of ProcessingJobRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: EntityId) -> ProcessingJob | None:
        """Retrieve ProcessingJob aggregate by ID."""
        stmt = select(ProcessingJobModel).where(ProcessingJobModel.id == str(id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[ProcessingJob]:
        """Find all ProcessingJobs in target Workspace."""
        stmt = select(ProcessingJobModel).where(
            ProcessingJobModel.workspace_id == str(workspace_id.value)
        )
        result = await self._session.execute(stmt)
        return [self._to_aggregate(m) for m in result.scalars().all()]

    async def find_by_document(self, document_id: DocumentId) -> list[ProcessingJob]:
        """Find all ProcessingJobs for a given Document."""
        stmt = select(ProcessingJobModel).where(
            ProcessingJobModel.document_id == str(document_id.value)
        )
        result = await self._session.execute(stmt)
        return [self._to_aggregate(m) for m in result.scalars().all()]

    async def save(self, aggregate: ProcessingJob) -> None:
        """Persist or update ProcessingJob aggregate root."""
        stmt = select(ProcessingJobModel).where(
            ProcessingJobModel.id == str(aggregate.id.value)
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = self._to_model(aggregate)
            self._session.add(model)
        else:
            existing.status = aggregate.status.value.value
            existing.error_message = aggregate.error_message
            existing.chunk_references_json = list(aggregate.chunk_references)
            existing.vector_references_json = list(aggregate.vector_references)
            existing.version = aggregate.version

            # Update tasks
            for t in aggregate.tasks:
                task_stmt = select(ProcessingTaskModel).where(
                    ProcessingTaskModel.id == str(t.id.value)
                )
                task_res = await self._session.execute(task_stmt)
                existing_task = task_res.scalar_one_or_none()
                if existing_task:
                    existing_task.status = t.status.value.value
                    existing_task.error_message = t.error_message
                    if t.result is not None:
                        existing_task.result_json = {
                            "output_count": t.result.output_count,
                            "execution_time_seconds": t.result.execution_time_seconds,
                            "metrics": t.result.metrics,
                            "metadata": t.result.metadata,
                        }

    async def delete(self, aggregate: ProcessingJob) -> None:
        """Delete ProcessingJob aggregate from persistence."""
        stmt = sql_delete(ProcessingJobModel).where(
            ProcessingJobModel.id == str(aggregate.id.value)
        )
        await self._session.execute(stmt)

    async def find(self, spec: Specification[ProcessingJob]) -> list[ProcessingJob]:
        """Find ProcessingJob aggregates satisfying specification filter."""
        stmt = select(ProcessingJobModel)
        result = await self._session.execute(stmt)
        aggregates = [self._to_aggregate(m) for m in result.scalars().all()]
        return [a for a in aggregates if spec.is_satisfied_by(a)]

    async def count(self, spec: Specification[ProcessingJob]) -> int:
        """Count ProcessingJob aggregates satisfying specification filter."""
        return len(await self.find(spec))

    def _to_model(self, aggregate: ProcessingJob) -> ProcessingJobModel:
        """Map domain ProcessingJob to ORM ProcessingJobModel."""
        chunking_json = {
            "strategy_type": aggregate.chunking_strategy.strategy_type,
            "chunk_size": aggregate.chunking_strategy.chunk_size,
            "chunk_overlap": aggregate.chunking_strategy.chunk_overlap,
        }

        embedding_json = {
            "model_name": aggregate.embedding_strategy.model_name,
            "dimension": aggregate.embedding_strategy.dimension,
        }

        tasks = []
        for t in aggregate.tasks:
            result_json = None
            if t.result is not None:
                result_json = {
                    "output_count": t.result.output_count,
                    "execution_time_seconds": t.result.execution_time_seconds,
                    "metrics": t.result.metrics,
                    "metadata": t.result.metadata,
                }
            tasks.append(
                ProcessingTaskModel(
                    id=str(t.id.value),
                    job_id=str(aggregate.id.value),
                    task_type=t.task_type.category.value,
                    order=t.order,
                    status=t.status.value.value,
                    error_message=t.error_message,
                    result_json=result_json,
                    created_at=t.created_at.value,
                )
            )

        return ProcessingJobModel(
            id=str(aggregate.id.value),
            workspace_id=str(aggregate.workspace_id.value),
            document_id=str(aggregate.document_id.value),
            status=aggregate.status.value.value,
            error_message=aggregate.error_message,
            chunking_strategy_json=chunking_json,
            embedding_strategy_json=embedding_json,
            chunk_references_json=list(aggregate.chunk_references),
            vector_references_json=list(aggregate.vector_references),
            version=aggregate.version,
            created_at=aggregate.created_at.value,
            tasks=tasks,
        )

    @staticmethod
    def _to_aggregate(model: ProcessingJobModel) -> ProcessingJob:
        """Map ORM ProcessingJobModel to domain ProcessingJob aggregate root."""
        created_at_dt = model.created_at
        if created_at_dt and created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=UTC)

        chunking_strat = ChunkingStrategy()
        if model.chunking_strategy_json:
            chunking_strat = ChunkingStrategy(
                strategy_type=model.chunking_strategy_json.get("strategy_type", "FIXED_SIZE"),
                chunk_size=model.chunking_strategy_json.get("chunk_size", 500),
                chunk_overlap=model.chunking_strategy_json.get("chunk_overlap", 50),
            )

        embedding_strat = EmbeddingStrategy()
        if model.embedding_strategy_json:
            embedding_strat = EmbeddingStrategy(
                model_name=model.embedding_strategy_json.get("model_name", "standard-text-embedding"),
                dimension=model.embedding_strategy_json.get("dimension", 768),
            )

        tasks = []
        for t in model.tasks:
            t_created = t.created_at
            if t_created and t_created.tzinfo is None:
                t_created = t_created.replace(tzinfo=UTC)

            result_vo = None
            if t.result_json:
                result_vo = ProcessingResult(
                    output_count=t.result_json.get("output_count", 0),
                    execution_time_seconds=t.result_json.get("execution_time_seconds", 0.0),
                    metrics=t.result_json.get("metrics", {}),
                    metadata=t.result_json.get("metadata", {}),
                )

            tasks.append(
                ProcessingTask(
                    id=EntityId(t.id),
                    task_type=ProcessingTaskType(TaskCategory(t.task_type)),
                    order=t.order,
                    status=ProcessingJobStatus(ProcessingJobStatusType(t.status)),
                    result=result_vo,
                    error_message=t.error_message,
                    created_at=Timestamp(t_created),
                )
            )

        return ProcessingJob(
            id=EntityId(model.id),
            workspace_id=WorkspaceId(model.workspace_id),
            document_id=DocumentId(model.document_id),
            status=ProcessingJobStatus(ProcessingJobStatusType(model.status)),
            chunking_strategy=chunking_strat,
            embedding_strategy=embedding_strat,
            tasks=tasks,
            chunk_references=tuple(model.chunk_references_json or []),
            vector_references=tuple(model.vector_references_json or []),
            error_message=model.error_message,
            created_at=Timestamp(created_at_dt),
            version=model.version,
        )
