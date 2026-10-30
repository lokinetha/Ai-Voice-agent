"""
ProcessingJob Aggregate Root for Processing Bounded Context.

Manages processing workflow and execution state for converting raw documents
into normalized chunk references and vector/embedding references.

Does NOT duplicate Knowledge domain entities (Document/Chunk). Store ONLY
references to resulting chunks/embeddings.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.aggregate_root import AggregateRoot
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import (
    DocumentId,
    EntityId,
    Timestamp,
    WorkspaceId,
)

from processing.domain.entities.processing_task import ProcessingTask
from processing.domain.events.processing_completed import ProcessingCompleted
from processing.domain.events.processing_failed import ProcessingFailed
from processing.domain.events.processing_started import ProcessingStarted
from processing.domain.value_objects.chunking_strategy import ChunkingStrategy
from processing.domain.value_objects.embedding_strategy import EmbeddingStrategy
from processing.domain.value_objects.processing_job_status import (
    ProcessingJobStatus,
)
from processing.domain.value_objects.processing_result import ProcessingResult
from processing.domain.value_objects.processing_task_type import TaskCategory


class ProcessingJob(AggregateRoot[EntityId]):
    """ProcessingJob Aggregate Root.

    Enforces invariants:
    - Workflow state transitions (PENDING -> RUNNING -> COMPLETED / FAILED).
    - Cannot execute tasks on completed or failed jobs.
    - Stores references to chunks and vectors without duplicating Knowledge objects.
    """

    def __init__(
        self,
        id: EntityId,
        workspace_id: WorkspaceId,
        document_id: DocumentId,
        status: ProcessingJobStatus | None = None,
        chunking_strategy: ChunkingStrategy | None = None,
        embedding_strategy: EmbeddingStrategy | None = None,
        tasks: Sequence[ProcessingTask] = (),
        chunk_references: Sequence[str] = (),
        vector_references: Sequence[str] = (),
        error_message: str = "",
        created_at: Timestamp | None = None,
        version: int = 1,
    ) -> None:
        super().__init__(id=id, created_at=created_at, version=version)

        self._workspace_id = workspace_id
        self._document_id = document_id
        self._status = status or ProcessingJobStatus.pending()
        self._chunking_strategy = chunking_strategy or ChunkingStrategy()
        self._embedding_strategy = embedding_strategy or EmbeddingStrategy()
        self._tasks: list[ProcessingTask] = list(tasks)
        self._chunk_references: list[str] = list(chunk_references)
        self._vector_references: list[str] = list(vector_references)
        self._error_message = error_message.strip()

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def workspace_id(self) -> WorkspaceId:
        return self._workspace_id

    @property
    def document_id(self) -> DocumentId:
        return self._document_id

    @property
    def status(self) -> ProcessingJobStatus:
        return self._status

    @property
    def chunking_strategy(self) -> ChunkingStrategy:
        return self._chunking_strategy

    @property
    def embedding_strategy(self) -> EmbeddingStrategy:
        return self._embedding_strategy

    @property
    def tasks(self) -> tuple[ProcessingTask, ...]:
        return tuple(self._tasks)

    @property
    def chunk_references(self) -> tuple[str, ...]:
        return tuple(self._chunk_references)

    @property
    def vector_references(self) -> tuple[str, ...]:
        return tuple(self._vector_references)

    @property
    def error_message(self) -> str:
        return self._error_message

    # ── Mutators ──────────────────────────────────────────────────────────

    def add_task(self, task: ProcessingTask) -> Result[None]:
        """Add a processing task to the job workflow."""
        if not self._status.is_pending:
            return Result.fail(Error("INVALID_STATE", "Cannot add tasks after job has started"))

        self._tasks.append(task)
        return Result.ok(None)

    def start(self) -> Result[None]:
        """Start the processing job."""
        if not self._status.is_pending:
            return Result.fail(Error("INVALID_STATE", "Only pending jobs can be started"))

        self._status = ProcessingJobStatus.running()
        for t in self._tasks:
            if t.order == 1:
                t.start()

        self._raise_event(
            ProcessingStarted(
                job_id=str(self.id.value),
                document_id=str(self._document_id.value),
                workspace_id=str(self._workspace_id.value),
            )
        )
        return Result.ok(None)

    def complete_task(
        self, category: TaskCategory, result: ProcessingResult
    ) -> Result[None]:
        """Mark a specific task category as completed."""
        if not self._status.is_running:
            return Result.fail(Error("INVALID_STATE", "Job must be running to complete tasks"))

        target_task = None
        for t in self._tasks:
            if t.task_type.category == category:
                target_task = t
                break

        if target_task is None:
            return Result.fail(Error("NOT_FOUND", f"Task of category '{category.value}' not found in job"))

        target_task.complete(result)

        # Advance next task if any
        next_order = target_task.order + 1
        for t in self._tasks:
            if t.order == next_order:
                t.start()

        return Result.ok(None)

    def complete_job(
        self, chunk_refs: Sequence[str], vector_refs: Sequence[str]
    ) -> Result[None]:
        """Complete the entire processing job storing references."""
        if not self._status.is_running:
            return Result.fail(Error("INVALID_STATE", "Only running jobs can be completed"))

        self._status = ProcessingJobStatus.completed()
        self._chunk_references = list(chunk_refs)
        self._vector_references = list(vector_refs)
        self._version += 1

        self._raise_event(
            ProcessingCompleted(
                job_id=str(self.id.value),
                document_id=str(self._document_id.value),
                chunk_count=len(self._chunk_references),
                vector_count=len(self._vector_references),
            )
        )
        return Result.ok(None)

    def fail_job(self, error_message: str) -> Result[None]:
        """Fail the processing job with an error message."""
        if self._status.is_completed or self._status.is_failed:
            return Result.fail(Error("INVALID_STATE", "Job is already terminal"))

        self._status = ProcessingJobStatus.failed()
        self._error_message = error_message.strip()
        self._version += 1

        self._raise_event(
            ProcessingFailed(
                job_id=str(self.id.value),
                document_id=str(self._document_id.value),
                error_message=self._error_message,
            )
        )
        return Result.ok(None)
