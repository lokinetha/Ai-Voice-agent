"""
FakeTTSAdapter implementing TTSPort.

Provider-independent fake Text-to-Speech adapter.
"""

from __future__ import annotations

from voice.domain.ports.tts_port import TTSPort
from voice.domain.value_objects.audio_format import AudioFormat


class FakeTTSAdapter(TTSPort):
    """Fake Text-to-Speech adapter."""

    async def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        audio_format: AudioFormat,
        language: str | None = None,
    ) -> bytes:
        """Synthesize text string into fake audio payload bytes."""
        lang_str = language or "en-IN"
        prefix = f"[TTS:{voice_id}:{lang_str}:{audio_format.sample_rate}Hz] ".encode()
        return prefix + text.encode("utf-8")
