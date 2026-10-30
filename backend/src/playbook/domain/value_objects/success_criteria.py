"""
SuccessCriteria Value Object.

Defines measurable success criteria for a Playbook.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class SuccessCriteria(ValueObject):
    """Immutable value object defining measurable criteria for playbook success.

    Attributes:
        primary_metric: The primary KPI name (e.g. "conversion_rate").
        target_value: Target value for the primary metric.
        secondary_metrics: Additional metric names to track.
        description: Human-readable description of what success looks like.
    """

    primary_metric: str = ""
    target_value: float = 0.0
    secondary_metrics: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""

    def _validate(self) -> None:
        if not self.primary_metric or not self.primary_metric.strip():
            raise ValueError("primary_metric cannot be empty")
        if self.target_value < 0.0:
            raise ValueError("target_value cannot be negative")
