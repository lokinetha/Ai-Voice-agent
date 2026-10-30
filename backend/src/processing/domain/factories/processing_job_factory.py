"""
ProcessingJobFactory for Processing Bounded Context.

Encapsulates construction of new ProcessingJob Aggregate Roots with standard tasks.
"""

from __future__ import annotations

from shared.kernel.value_objects import DocumentId, EntityId, WorkspaceId

from processing.domain.entities.processing_job import ProcessingJob
from processing.domain.entities.processing_task import ProcessingTask
from processing.domain.value_objects.chunking_strategy import ChunkingStrategy
from processing.domain.value_objects.embedding_strategy import EmbeddingStrategy
from processing.domain.value_objects.processing_task_type import (
    ProcessingTaskType,
)


class ProcessingJobFactory:
    """Factory constructing new ProcessingJob Aggregate Roots."""

    @classmethod
    def create(
        cls,
        workspace_id: WorkspaceId,
        document_id: DocumentId,
        chunking_strategy: ChunkingStrategy | None = None,
        embedding_strategy: EmbeddingStrategy | None = None,
        job_id: EntityId | None = None,
    ) -> ProcessingJob:
        """Create and initialize a new ProcessingJob aggregate root with standard workflow tasks.

        Tasks initialized:
        1. PARSING
        2. CHUNKING
        3. EMBEDDING
        4. INDEXING

        Args:
            workspace_id: Owning WorkspaceId.
            document_id: Target DocumentId.
            chunking_strategy: Optional ChunkingStrategy.
            embedding_strategy: Optional EmbeddingStrategy.
            job_id: Optional explicit job EntityId.

        Returns:
            Initialized ProcessingJob aggregate root.
        """
        id_val = job_id or EntityId()

        tasks = [
            ProcessingTask(
                id=EntityId(),
                task_type=ProcessingTaskType.parsing(),
                order=1,
            ),
            ProcessingTask(
                id=EntityId(),
                task_type=ProcessingTaskType.chunking(),
                order=2,
            ),
            ProcessingTask(
                id=EntityId(),
                task_type=ProcessingTaskType.embedding(),
                order=3,
            ),
            ProcessingTask(
                id=EntityId(),
                task_type=ProcessingTaskType.indexing(),
                order=4,
            ),
        ]

        job = ProcessingJob(
            id=id_val,
            workspace_id=workspace_id,
            document_id=document_id,
            chunking_strategy=chunking_strategy or ChunkingStrategy(),
            embedding_strategy=embedding_strategy or EmbeddingStrategy(),
            tasks=tasks,
        )

        return job
