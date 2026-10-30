"""
AudioChunk Value Object.

Represents a single transient segment of audio data in a real-time stream.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class AudioChunk(ValueObject):
    """Immutable audio payload chunk for real-time streaming.

    Attributes:
        payload: Binary audio bytes.
        sequence_number: Sequential packet index.
        duration_ms: Duration of audio snippet in milliseconds.
        is_final: Flag indicating end of turn/stream segment.
    """

    payload: bytes = b""
    sequence_number: int = 0
    duration_ms: int = 20
    is_final: bool = False

    def _validate(self) -> None:
        if self.sequence_number < 0:
            raise ValueError("sequence_number cannot be negative")
        if self.duration_ms < 0:
            raise ValueError("duration_ms cannot be negative")
