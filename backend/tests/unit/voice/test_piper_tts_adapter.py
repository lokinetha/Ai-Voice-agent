"""
Unit and Integration tests for PiperTTSAdapter.

Tests successful synthesis, metadata, WAV header validity, missing model file handling,
and empty text handling using mock engine injection and Python's standard wave module.
"""

from __future__ import annotations

import asyncio
import io
import os
import unittest
import wave

from shared.config.settings import settings
from voice.domain.value_objects.audio_format import AudioFormat
from voice.infrastructure.adapters.local_tts_adapter import (
    LocalTTSAdapter,
    TTSProviderError,
)
from voice.infrastructure.adapters.piper_tts_adapter import (
    PiperTTSAdapter,
    create_pcm_wav_bytes,
)


class MockPiperEngine:
    """Mock PiperVoice engine producing synthetic audio samples for unit tests."""

    def __init__(self, sample_bytes: bytes = b"\x00\x01\x02\x03" * 250) -> None:
        self.sample_bytes = sample_bytes

    def synthesize_bytes(
        self, text: str, voice_id: str, audio_format: AudioFormat
    ) -> bytes:
        return self.sample_bytes


class TestPiperTTSAdapter(unittest.TestCase):
    """Unit test suite for PiperTTSAdapter."""

    def test_synthesize_speech_produces_valid_wav_format(self) -> None:
        """Verify that synthesize_speech returns a valid WAV readable by wave module."""
        async def run() -> None:
            mock_engine = MockPiperEngine()
            adapter = PiperTTSAdapter(
                model_path="/fake/path/model.onnx",
                piper_engine=mock_engine,
            )

            fmt = AudioFormat(sample_rate=22050)
            audio_bytes = await adapter.synthesize_speech(
                text="Hello, this is a test.",
                voice_id="default",
                audio_format=fmt,
            )

            self.assertTrue(len(audio_bytes) > 44)

            # Validate WAV format using Python's standard wave module
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                self.assertGreater(wf.getnchannels(), 0)
                self.assertGreater(wf.getsampwidth(), 0)
                self.assertGreater(wf.getframerate(), 0)
                self.assertGreater(wf.getnframes(), 0)

        asyncio.run(run())

    def test_synthesize_detailed_metadata_and_duration(self) -> None:
        """Verify detailed synthesis result metadata."""
        async def run() -> None:
            mock_engine = MockPiperEngine()
            adapter = PiperTTSAdapter(
                length_scale=1.1,
                noise_scale=0.6,
                piper_engine=mock_engine,
            )

            fmt = AudioFormat(sample_rate=22050)
            res = await adapter.synthesize_detailed(
                text="Testing detailed Piper metadata",
                voice_id="default",
                audio_format=fmt,
            )

            self.assertEqual(res.audio_format.sample_rate, 22050)
            self.assertGreater(res.duration_seconds, 0.0)
            self.assertGreaterEqual(res.latency_ms, 0.0)

            # Verify WAV structure
            with wave.open(io.BytesIO(res.audio_bytes), "rb") as wf:
                self.assertEqual(wf.getnchannels(), 1)
                self.assertEqual(wf.getsampwidth(), 2)
                self.assertEqual(wf.getframerate(), 22050)
                self.assertGreater(wf.getnframes(), 0)

        asyncio.run(run())

    def test_create_pcm_wav_bytes_helper(self) -> None:
        """Verify standalone create_pcm_wav_bytes helper function."""
        pcm_frames = b"\x00\x00" * 500
        wav_bytes = create_pcm_wav_bytes(pcm_frames, sample_rate=16000, channels=1, sample_width=2)

        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)
            self.assertEqual(wf.getframerate(), 16000)
            self.assertEqual(wf.getnframes(), 500)

    def test_missing_model_file_failure(self) -> None:
        """Verify missing model file raises TTSProviderError with MODEL_NOT_FOUND code."""
        async def run() -> None:
            adapter = PiperTTSAdapter(model_path="/non_existent_path/piper_model.onnx")
            fmt = AudioFormat()

            with self.assertRaises(TTSProviderError) as ctx:
                await adapter.synthesize_speech("Test text", "default", fmt)

            self.assertEqual(ctx.exception.code, "MODEL_NOT_FOUND")

        asyncio.run(run())

    def test_empty_text_failure(self) -> None:
        """Verify empty text input raises TTSProviderError with INVALID_TEXT code."""
        async def run() -> None:
            adapter = PiperTTSAdapter(piper_engine=MockPiperEngine())
            fmt = AudioFormat()

            with self.assertRaises(TTSProviderError) as ctx:
                await adapter.synthesize_speech("", "default", fmt)

            self.assertEqual(ctx.exception.code, "INVALID_TEXT")

        asyncio.run(run())

    def test_existing_local_tts_adapter_remains_functional(self) -> None:
        """Verify existing LocalTTSAdapter (pyttsx3 fallback) produces valid WAV."""
        async def run() -> None:
            adapter = LocalTTSAdapter()
            fmt = AudioFormat()
            audio_bytes = await adapter.synthesize_speech("Fallback pyttsx3 test", "default", fmt)

            self.assertTrue(len(audio_bytes) > 0)
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                self.assertGreater(wf.getnchannels(), 0)
                self.assertGreater(wf.getsampwidth(), 0)
                self.assertGreater(wf.getframerate(), 0)
                self.assertGreater(wf.getnframes(), 0)

        asyncio.run(run())

    @unittest.skipUnless(
        bool(settings.piper_model_path and os.path.exists(settings.piper_model_path)),
        "Piper model file not configured on disk",
    )
    def test_live_piper_integration_if_model_configured(self) -> None:
        """Integration test executing real Piper model if configured on disk."""
        async def run() -> None:
            adapter = PiperTTSAdapter(
                model_path=settings.piper_model_path,
                config_path=settings.piper_config_path,
            )
            fmt = AudioFormat(sample_rate=22050)
            audio = await adapter.synthesize_speech("Hello, this is a direct Piper synthesis test.", "default", fmt)

            self.assertTrue(len(audio) > 44)
            with wave.open(io.BytesIO(audio), "rb") as wf:
                self.assertGreater(wf.getnchannels(), 0)
                self.assertGreater(wf.getsampwidth(), 0)
                self.assertGreater(wf.getframerate(), 0)
                self.assertGreater(wf.getnframes(), 0)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
