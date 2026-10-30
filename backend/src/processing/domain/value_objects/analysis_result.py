"""
AnalysisResult Value Object.

Captures outcome statistics and metadata of a completed ConversationAnalysis job.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class AnalysisResult(ValueObject):
    """Immutable value object containing conversation analysis execution outcome.

    Attributes:
        signals_count: Total behavioral signals detected.
        patterns_count: Total conversation patterns detected.
        execution_time_seconds: Duration of analysis execution.
        summary: Human-readable narrative summary.
        metadata: Additional contextual metadata dictionary.
    """

    signals_count: int = 0
    patterns_count: int = 0
    execution_time_seconds: float = 0.0
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def _validate(self) -> None:
        if self.signals_count < 0:
            raise ValueError("signals_count cannot be negative")
        if self.patterns_count < 0:
            raise ValueError("patterns_count cannot be negative")
        if self.execution_time_seconds < 0.0:
            raise ValueError("execution_time_seconds cannot be negative")
