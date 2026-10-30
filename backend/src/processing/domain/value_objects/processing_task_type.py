"""
ProcessingTaskType Value Object.

Categorizes the type of task within a ProcessingJob workflow.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


class TaskCategory(enum.Enum):
    """Task category enumeration."""

    PARSING = "PARSING"
    OCR = "OCR"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    INDEXING = "INDEXING"


@dataclass(frozen=True)
class ProcessingTaskType(ValueObject):
    """Immutable value object categorizing a processing task."""

    category: TaskCategory = TaskCategory.PARSING

    def _validate(self) -> None:
        if not isinstance(self.category, TaskCategory):
            raise ValueError(f"Invalid TaskCategory: {self.category}")

    @classmethod
    def parsing(cls) -> ProcessingTaskType:
        return cls(TaskCategory.PARSING)

    @classmethod
    def ocr(cls) -> ProcessingTaskType:
        return cls(TaskCategory.OCR)

    @classmethod
    def chunking(cls) -> ProcessingTaskType:
        return cls(TaskCategory.CHUNKING)

    @classmethod
    def embedding(cls) -> ProcessingTaskType:
        return cls(TaskCategory.EMBEDDING)

    @classmethod
    def indexing(cls) -> ProcessingTaskType:
        return cls(TaskCategory.INDEXING)
