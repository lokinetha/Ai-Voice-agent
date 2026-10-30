"""
FakeSTTAdapter implementing STTPort.

Provider-independent fake Speech-to-Text adapter for testing and production workflow without vendor SDKs.
"""

from __future__ import annotations

from voice.domain.ports.stt_port import STTPort
from voice.domain.value_objects.audio_chunk import AudioChunk
from voice.domain.value_objects.audio_format import AudioFormat
from voice.infrastructure.adapters.local_whisper_stt_adapter import (
    WhisperTranscriptionResult,
    is_telugu_text,
)


class FakeSTTAdapter(STTPort):
    """Fake Speech-to-Text adapter."""

    async def transcribe_audio_chunk(
        self,
        chunk: AudioChunk,
        audio_format: AudioFormat,
        language: str | None = None,
    ) -> tuple[str, float]:
        """Return deterministic transcript for input chunk payload."""
        res = await self.transcribe_detailed(chunk, audio_format, language)
        return res.text, res.confidence

    async def transcribe_detailed(
        self,
        chunk: AudioChunk,
        audio_format: AudioFormat,
        language: str | None = None,
    ) -> WhisperTranscriptionResult:
        """Return detailed fake transcription result."""
        if not chunk.payload:
            return WhisperTranscriptionResult(
                text="", confidence=1.0, language=language or "en-IN"
            )

        raw_text = chunk.payload.decode("utf-8", errors="ignore").strip()
        lang = "te-IN" if is_telugu_text(raw_text) else (language if (language and language != "auto") else "en-IN")

        if raw_text:
            return WhisperTranscriptionResult(
                text=raw_text, confidence=0.95, language=lang
            )

        return WhisperTranscriptionResult(
            text=f"Transcribed speech payload chunk #{chunk.sequence_number}",
            confidence=0.90,
            language=lang,
        )
