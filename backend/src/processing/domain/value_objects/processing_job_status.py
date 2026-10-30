"""
ProcessingJobStatus Value Object.

Represents the state of a document processing job.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


class ProcessingJobStatusType(enum.Enum):
    """Job status enumeration."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class ProcessingJobStatus(ValueObject):
    """Immutable value object for job status."""

    value: ProcessingJobStatusType = ProcessingJobStatusType.PENDING

    def _validate(self) -> None:
        if not isinstance(self.value, ProcessingJobStatusType):
            raise ValueError(f"Invalid ProcessingJobStatus: {self.value}")

    @property
    def is_pending(self) -> bool:
        return self.value == ProcessingJobStatusType.PENDING

    @property
    def is_running(self) -> bool:
        return self.value == ProcessingJobStatusType.RUNNING

    @property
    def is_completed(self) -> bool:
        return self.value == ProcessingJobStatusType.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.value == ProcessingJobStatusType.FAILED

    @property
    def is_cancelled(self) -> bool:
        return self.value == ProcessingJobStatusType.CANCELLED

    @classmethod
    def pending(cls) -> ProcessingJobStatus:
        return cls(ProcessingJobStatusType.PENDING)

    @classmethod
    def running(cls) -> ProcessingJobStatus:
        return cls(ProcessingJobStatusType.RUNNING)

    @classmethod
    def completed(cls) -> ProcessingJobStatus:
        return cls(ProcessingJobStatusType.COMPLETED)

    @classmethod
    def failed(cls) -> ProcessingJobStatus:
        return cls(ProcessingJobStatusType.FAILED)

    @classmethod
    def cancelled(cls) -> ProcessingJobStatus:
        return cls(ProcessingJobStatusType.CANCELLED)
