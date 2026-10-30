"""
TTSPort Interface for Voice Bounded Context.

Abstract port for Text-to-Speech synthesis.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from voice.domain.value_objects.audio_format import AudioFormat


class TTSPort(ABC):
    """Abstract port for Text-to-Speech synthesis."""

    @abstractmethod
    async def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        audio_format: AudioFormat,
        language: str | None = None,
    ) -> bytes:
        """Synthesize text into speech audio bytes.

        Args:
            text: Input text string.
            voice_id: Identifier of target voice model/voice.
            audio_format: Target AudioFormat.
            language: Optional target language code (e.g. 'en', 'te', 'en-IN', 'te-IN').

        Returns:
            Synthesized audio bytes.
        """
        ...
