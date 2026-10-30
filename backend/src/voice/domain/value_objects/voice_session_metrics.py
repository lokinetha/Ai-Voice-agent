"""
VoiceSessionMetrics Value Object.

Tracks quantitative operational metrics for a VoiceSession.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class VoiceSessionMetrics(ValueObject):
    """Immutable voice session metrics container.

    Attributes:
        total_turns: Number of voice turns completed.
        audio_duration_seconds: Total duration of processed audio.
        average_latency_ms: Average processing latency across turns.
        stt_latency_ms: STT processing latency.
        tts_latency_ms: TTS processing latency.
    """

    total_turns: int = 0
    audio_duration_seconds: float = 0.0
    average_latency_ms: float = 0.0
    stt_latency_ms: float = 0.0
    tts_latency_ms: float = 0.0

    def _validate(self) -> None:
        if self.total_turns < 0:
            raise ValueError("total_turns cannot be negative")
        if self.audio_duration_seconds < 0.0:
            raise ValueError("audio_duration_seconds cannot be negative")
        if self.average_latency_ms < 0.0:
            raise ValueError("average_latency_ms cannot be negative")
