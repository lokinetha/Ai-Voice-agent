"""
ProcessingJobMapper for mapping between Domain ProcessingJob aggregate and DTOs.
"""

from __future__ import annotations

from processing.application.dto.processing_dto import (
    ChunkingStrategyDTO,
    EmbeddingStrategyDTO,
    ProcessingJobDTO,
    ProcessingResultDTO,
    ProcessingTaskDTO,
)
from processing.domain.entities.processing_job import ProcessingJob
from processing.domain.entities.processing_task import ProcessingTask


class ProcessingJobMapper:
    """Static mapper converting ProcessingJob domain entities to DTOs."""

    @staticmethod
    def to_dto(job: ProcessingJob) -> ProcessingJobDTO:
        """Map ProcessingJob aggregate root to ProcessingJobDTO."""
        chunking_dto = ChunkingStrategyDTO(
            strategy_type=job.chunking_strategy.strategy_type,
            chunk_size=job.chunking_strategy.chunk_size,
            chunk_overlap=job.chunking_strategy.chunk_overlap,
        )

        embedding_dto = EmbeddingStrategyDTO(
            model_name=job.embedding_strategy.model_name,
            dimension=job.embedding_strategy.dimension,
        )

        task_dtos = tuple(ProcessingJobMapper.to_task_dto(t) for t in job.tasks)

        return ProcessingJobDTO(
            id=str(job.id.value),
            workspace_id=str(job.workspace_id.value),
            document_id=str(job.document_id.value),
            status=job.status.value.value,
            chunking_strategy=chunking_dto,
            embedding_strategy=embedding_dto,
            tasks=task_dtos,
            chunk_references=job.chunk_references,
            vector_references=job.vector_references,
            error_message=job.error_message,
            version=job.version,
            created_at=job.created_at.value,
        )

    @staticmethod
    def to_task_dto(task: ProcessingTask) -> ProcessingTaskDTO:
        """Map ProcessingTask entity to ProcessingTaskDTO."""
        result_dto = None
        if task.result is not None:
            result_dto = ProcessingResultDTO(
                output_count=task.result.output_count,
                execution_time_seconds=task.result.execution_time_seconds,
                metrics=task.result.metrics,
                metadata=task.result.metadata,
            )

        return ProcessingTaskDTO(
            id=str(task.id.value),
            task_type=task.task_type.category.value,
            order=task.order,
            status=task.status.value.value,
            result=result_dto,
            error_message=task.error_message,
        )
