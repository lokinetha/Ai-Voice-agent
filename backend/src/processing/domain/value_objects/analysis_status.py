"""
AnalysisStatus Value Object.

Represents the state of a ConversationAnalysis execution.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


class AnalysisStatusType(enum.Enum):
    """Analysis status enumeration."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class AnalysisStatus(ValueObject):
    """Immutable value object for analysis status."""

    value: AnalysisStatusType = AnalysisStatusType.PENDING

    def _validate(self) -> None:
        if not isinstance(self.value, AnalysisStatusType):
            raise ValueError(f"Invalid AnalysisStatus: {self.value}")

    @property
    def is_pending(self) -> bool:
        return self.value == AnalysisStatusType.PENDING

    @property
    def is_in_progress(self) -> bool:
        return self.value == AnalysisStatusType.IN_PROGRESS

    @property
    def is_completed(self) -> bool:
        return self.value == AnalysisStatusType.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.value == AnalysisStatusType.FAILED

    @classmethod
    def pending(cls) -> AnalysisStatus:
        return cls(AnalysisStatusType.PENDING)

    @classmethod
    def in_progress(cls) -> AnalysisStatus:
        return cls(AnalysisStatusType.IN_PROGRESS)

    @classmethod
    def completed(cls) -> AnalysisStatus:
        return cls(AnalysisStatusType.COMPLETED)

    @classmethod
    def failed(cls) -> AnalysisStatus:
        return cls(AnalysisStatusType.FAILED)
