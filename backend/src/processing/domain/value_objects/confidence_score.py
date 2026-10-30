"""
ConfidenceScore Value Object.

Represents a normalized confidence score between 0.0 and 1.0 for detected behavioral signals and patterns.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class ConfidenceScore(ValueObject):
    """Immutable value object for normalized confidence score [0.0, 1.0]."""

    value: float = 1.0

    def _validate(self) -> None:
        if not isinstance(self.value, (int, float)) or not (0.0 <= float(self.value) <= 1.0):
            raise ValueError(f"ConfidenceScore must be a float between 0.0 and 1.0, got: {self.value}")

    def to_percentage(self) -> float:
        """Return confidence score as rounded percentage."""
        return round(self.value * 100, 2)
