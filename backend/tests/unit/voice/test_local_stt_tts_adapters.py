"""
Unit tests for LocalWhisperSTTAdapter and LocalTTSAdapter.

Tests successful transcription, synthesis, invalid input handling, and metadata
without external network calls or downloading large ML models.
"""

from __future__ import annotations

import asyncio
import unittest

from voice.domain.value_objects.audio_chunk import AudioChunk
from voice.domain.value_objects.audio_format import AudioFormat
from voice.infrastructure.adapters.local_tts_adapter import (
    LocalTTSAdapter,
    TTSProviderError,
)
from voice.infrastructure.adapters.local_whisper_stt_adapter import (
    LocalWhisperSTTAdapter,
    STTProviderError,
)


class MockWhisperEngine:
    """Mock engine simulating Whisper transcription without model downloads."""

    def __init__(self, text: str = "Hello from local Whisper", confidence: float = 0.96) -> None:
        self.text = text
        self.confidence = confidence

    def transcribe_bytes(self, payload: bytes) -> dict[str, object]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "language": "en",
            "duration": 1.5,
        }


class MockTTSEngine:
    """Mock engine simulating TTS synthesis without hardware audio calls."""

    def __init__(self, pcm_data: bytes = b"MOCK_AUDIO_SYNTHESIS") -> None:
        self.pcm_data = pcm_data

    def synthesize_bytes(
        self, text: str, voice_id: str, audio_format: AudioFormat
    ) -> bytes:
        return b"RIFF_MOCK_HEADER_" + self.pcm_data


class TestLocalSTTAdapter(unittest.TestCase):
    """Unit test suite for LocalWhisperSTTAdapter."""

    def test_transcribe_audio_chunk_success(self) -> None:
        async def run() -> None:
            mock_engine = MockWhisperEngine(text="Transcribed speech text", confidence=0.98)
            adapter = LocalWhisperSTTAdapter(
                model_name="tiny",
                model_engine=mock_engine,
            )

            chunk = AudioChunk(payload=b"RIFF_PCM_HEADER_DATA_1234", sequence_number=1)
            fmt = AudioFormat(sample_rate=16000)

            text, confidence = await adapter.transcribe_audio_chunk(chunk, fmt)
            self.assertEqual(text, "Transcribed speech text")
            self.assertEqual(confidence, 0.98)

        asyncio.run(run())

    def test_transcribe_detailed_metadata(self) -> None:
        async def run() -> None:
            mock_engine = MockWhisperEngine(text="Detailed transcript test", confidence=0.92)
            adapter = LocalWhisperSTTAdapter(model_engine=mock_engine)

            chunk = AudioChunk(payload=b"RIFF_PCM_HEADER_DATA_5678", sequence_number=1)
            fmt = AudioFormat(sample_rate=16000)

            res = await adapter.transcribe_detailed(chunk, fmt)
            self.assertEqual(res.text, "Detailed transcript test")
            self.assertEqual(res.confidence, 0.92)
            self.assertEqual(res.language, "en")
            self.assertGreaterEqual(res.latency_ms, 0.0)

        asyncio.run(run())

    def test_transcribe_empty_payload_failure(self) -> None:
        async def run() -> None:
            adapter = LocalWhisperSTTAdapter(model_engine=MockWhisperEngine())
            chunk = AudioChunk(payload=b"", sequence_number=1)
            fmt = AudioFormat()

            with self.assertRaises(STTProviderError) as ctx:
                await adapter.transcribe_audio_chunk(chunk, fmt)
            self.assertEqual(ctx.exception.code, "INVALID_AUDIO")

        asyncio.run(run())


class TestLocalTTSAdapter(unittest.TestCase):
    """Unit test suite for LocalTTSAdapter."""

    def test_synthesize_speech_success(self) -> None:
        async def run() -> None:
            mock_engine = MockTTSEngine(pcm_data=b"AUDIO_DATA_PAYLOAD")
            adapter = LocalTTSAdapter(
                voice_id="english_female",
                rate=160,
                volume=0.9,
                tts_engine=mock_engine,
            )

            fmt = AudioFormat(sample_rate=22050)
            audio_bytes = await adapter.synthesize_speech(
                text="Hello local synthesis",
                voice_id="english_female",
                audio_format=fmt,
            )

            self.assertTrue(len(audio_bytes) > 0)
            self.assertIn(b"AUDIO_DATA_PAYLOAD", audio_bytes)

        asyncio.run(run())

    def test_synthesize_detailed_metadata(self) -> None:
        async def run() -> None:
            mock_engine = MockTTSEngine(pcm_data=b"DETAILED_AUDIO")
            adapter = LocalTTSAdapter(tts_engine=mock_engine)

            fmt = AudioFormat(sample_rate=16000)
            res = await adapter.synthesize_detailed(
                text="Detailed TTS synthesis test",
                voice_id="default",
                audio_format=fmt,
            )

            self.assertIn(b"DETAILED_AUDIO", res.audio_bytes)
            self.assertEqual(res.audio_format.sample_rate, 16000)
            self.assertGreater(res.duration_seconds, 0.0)
            self.assertGreaterEqual(res.latency_ms, 0.0)

        asyncio.run(run())

    def test_synthesize_empty_text_failure(self) -> None:
        async def run() -> None:
            adapter = LocalTTSAdapter(tts_engine=MockTTSEngine())
            fmt = AudioFormat()

            with self.assertRaises(TTSProviderError) as ctx:
                await adapter.synthesize_speech("", "default", fmt)
            self.assertEqual(ctx.exception.code, "INVALID_TEXT")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
