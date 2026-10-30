"""
ProcessingTask Entity for Processing Bounded Context.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp

from processing.domain.value_objects.processing_job_status import (
    ProcessingJobStatus,
)
from processing.domain.value_objects.processing_result import ProcessingResult
from processing.domain.value_objects.processing_task_type import (
    ProcessingTaskType,
)


class ProcessingTask(Entity[EntityId]):
    """Specific step/task within a document ProcessingJob workflow."""

    def __init__(
        self,
        id: EntityId,
        task_type: ProcessingTaskType,
        order: int = 1,
        status: ProcessingJobStatus | None = None,
        result: ProcessingResult | None = None,
        error_message: str = "",
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if order < 1:
            raise ValueError("ProcessingTask order must be >= 1")

        self._task_type = task_type
        self._order = order
        self._status = status or ProcessingJobStatus.pending()
        self._result = result
        self._error_message = error_message.strip()

    @property
    def task_type(self) -> ProcessingTaskType:
        return self._task_type

    @property
    def order(self) -> int:
        return self._order

    @property
    def status(self) -> ProcessingJobStatus:
        return self._status

    @property
    def result(self) -> ProcessingResult | None:
        return self._result

    @property
    def error_message(self) -> str:
        return self._error_message

    def start(self) -> None:
        """Mark task as running."""
        self._status = ProcessingJobStatus.running()

    def complete(self, result: ProcessingResult) -> None:
        """Mark task as completed with result."""
        self._status = ProcessingJobStatus.completed()
        self._result = result

    def fail(self, error_message: str) -> None:
        """Mark task as failed."""
        self._status = ProcessingJobStatus.failed()
        self._error_message = error_message.strip()
