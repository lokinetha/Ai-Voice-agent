"""
Integration tests for FasterWhisperSTTAdapter.

Runs model-dependent integration tests on GPU/CUDA when models/faster-whisper-large-v3 is present.
Skips cleanly if model or CUDA environment is unavailable.
"""

from __future__ import annotations

import asyncio
import os
import unittest

from shared.config.settings import settings
from voice.domain.value_objects.audio_chunk import AudioChunk
from voice.domain.value_objects.audio_format import AudioFormat
from voice.infrastructure.adapters.faster_whisper_stt_adapter import (
    FasterWhisperSTTAdapter,
)
from voice.infrastructure.adapters.local_whisper_stt_adapter import is_telugu_text

# Resolve model path
MODEL_PATH = str(settings.project_root / "models" / "faster-whisper-large-v3")
HAS_MODEL = os.path.exists(MODEL_PATH)
TELUGU_WAV_PATH = str(settings.project_root / "telugu_input.wav")
ENGLISH_WAV_PATH = str(settings.project_root / "sample_input.wav")


@unittest.skipUnless(HAS_MODEL, "faster-whisper large-v3 model not found on disk at models/faster-whisper-large-v3")
class TestFasterWhisperIntegration(unittest.TestCase):
    """Hardware and GPU integration test for FasterWhisperSTTAdapter."""

    def setUp(self) -> None:
        """Initialize FasterWhisperSTTAdapter configured for CUDA large-v3."""
        self.adapter = FasterWhisperSTTAdapter(
            model_path=MODEL_PATH,
            device="cuda",
            compute_type="int8_float16",
        )

    def test_cuda_faster_whisper_telugu_transcription(self) -> None:
        """Integration test: Transcribe Telugu speech audio with large-v3 on CUDA."""
        if not os.path.exists(TELUGU_WAV_PATH):
            self.skipTest(f"Telugu audio file not found at '{TELUGU_WAV_PATH}'")

        with open(TELUGU_WAV_PATH, "rb") as f:
            audio_bytes = f.read()

        async def run() -> None:
            chunk = AudioChunk(payload=audio_bytes)
            fmt = AudioFormat(sample_rate=16000)

            res = await self.adapter.transcribe_detailed(chunk, fmt, language="auto")

            self.assertEqual(res.language, "te-IN")
            self.assertTrue(len(res.text.strip()) > 0)
            self.assertTrue(is_telugu_text(res.text))
            self.assertGreater(res.confidence, 0.5)

        asyncio.run(run())

    def test_cuda_faster_whisper_english_transcription(self) -> None:
        """Integration test: Transcribe English speech audio with large-v3 on CUDA."""
        if not os.path.exists(ENGLISH_WAV_PATH):
            self.skipTest(f"English audio file not found at '{ENGLISH_WAV_PATH}'")

        with open(ENGLISH_WAV_PATH, "rb") as f:
            audio_bytes = f.read()

        async def run() -> None:
            chunk = AudioChunk(payload=audio_bytes)
            fmt = AudioFormat(sample_rate=16000)

            res = await self.adapter.transcribe_detailed(chunk, fmt, language="en-IN")

            self.assertEqual(res.language, "en-IN")
            self.assertTrue(len(res.text.strip()) > 0)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
