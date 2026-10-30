"""
STTPort Interface for Voice Bounded Context.

Abstract port for Speech-to-Text transcription.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from voice.domain.value_objects.audio_chunk import AudioChunk
from voice.domain.value_objects.audio_format import AudioFormat


class STTPort(ABC):
    """Abstract port for Speech-to-Text transcription."""

    @abstractmethod
    async def transcribe_audio_chunk(
        self,
        chunk: AudioChunk,
        audio_format: AudioFormat,
        language: str | None = None,
    ) -> tuple[str, float]:
        """Transcribe an audio chunk into text.

        Args:
            chunk: AudioChunk payload.
            audio_format: AudioFormat configuration.
            language: Optional target language code (e.g. 'en', 'te', 'auto').

        Returns:
            Tuple of (transcript_text, confidence_score).
        """
        ...
