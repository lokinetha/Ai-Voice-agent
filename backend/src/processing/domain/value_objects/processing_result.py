"""
ProcessingResult Value Object.

Captures outcome statistics and metadata of a completed processing task or job.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class ProcessingResult(ValueObject):
    """Immutable value object containing task execution outcome details.

    Attributes:
        output_count: Total items produced (e.g. chunks or vectors).
        execution_time_seconds: Duration of execution.
        metrics: Dictionary of numerical metrics.
        metadata: Dictionary of additional output references/metadata.
    """

    output_count: int = 0
    execution_time_seconds: float = 0.0
    metrics: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def _validate(self) -> None:
        if self.output_count < 0:
            raise ValueError("output_count cannot be negative")
        if self.execution_time_seconds < 0.0:
            raise ValueError("execution_time_seconds cannot be negative")
