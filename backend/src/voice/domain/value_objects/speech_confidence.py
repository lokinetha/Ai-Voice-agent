"""
SpeechConfidence Value Object.

Represents transcription confidence score [0.0, 1.0].
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class SpeechConfidence(ValueObject):
    """Immutable value object for speech recognition confidence score."""

    value: float = 1.0

    def _validate(self) -> None:
        if not isinstance(self.value, (int, float)) or not (0.0 <= float(self.value) <= 1.0):
            raise ValueError(f"SpeechConfidence must be a float between 0.0 and 1.0, got: {self.value}")
