"""
Unit tests for FasterWhisperSTTAdapter.

Verifies:
1. Model path configuration.
2. Lazy model loading.
3. Model reused across multiple transcriptions.
4. Explicit English language normalization.
5. Explicit Telugu language normalization.
6. Auto language detection.
7. task="transcribe".
8. beam_size=5.
9. temperature=0.
10. Model-not-found error.
11. Model-load failure.
12. Transcription failure.
13. Provider-independent result mapping.
14. No raw faster-whisper exceptions leaking outside infrastructure.
"""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from shared.config.settings import settings
from voice.domain.value_objects.audio_chunk import AudioChunk
from voice.domain.value_objects.audio_format import AudioFormat
from voice.infrastructure.adapters.faster_whisper_stt_adapter import (
    FasterWhisperSTTAdapter,
    map_whisper_language_to_locale,
    normalize_faster_whisper_input_language,
)
from voice.infrastructure.adapters.local_whisper_stt_adapter import (
    STTProviderError,
    WhisperTranscriptionResult,
)


class MockSegment:
    """Mock Segment object returned by faster-whisper transcribe."""

    def __init__(self, text: str) -> None:
        self.text = text


class MockTranscriptionInfo:
    """Mock Info object returned by faster-whisper transcribe."""

    def __init__(self, language: str = "te", probability: float = 0.98, duration: float = 2.5) -> None:
        self.language = language
        self.language_probability = probability
        self.duration = duration


class MockWhisperModelEngine:
    """Mock WhisperModel engine capturing call arguments without transcribe_bytes attribute."""

    def __init__(self, text: str = "నమస్కారం", language: str = "te") -> None:
        self.text = text
        self.language = language
        self.last_transcribe_kwargs: dict[str, str | int | float | None] = {}
        self.call_count = 0

    def transcribe(
        self,
        audio: str,
        language: str | None = None,
        task: str = "transcribe",
        beam_size: int = 5,
        temperature: float = 0.0,
    ) -> tuple[list[MockSegment], MockTranscriptionInfo]:
        self.call_count += 1
        self.last_transcribe_kwargs = {
            "audio": audio,
            "language": language,
            "task": task,
            "beam_size": beam_size,
            "temperature": temperature,
        }
        return [MockSegment(self.text)], MockTranscriptionInfo(language=self.language)


class FailingMockEngine:
    """Mock WhisperModel engine raising errors during transcribe call."""

    def __init__(self, exception_to_raise: Exception) -> None:
        self._exc = exception_to_raise

    def transcribe(self, *args: object, **kwargs: object) -> tuple[list[MockSegment], MockTranscriptionInfo]:
        raise self._exc


class TestFasterWhisperSTTAdapter(unittest.TestCase):
    """Unit test suite for FasterWhisperSTTAdapter."""

    def test_model_path_configuration(self) -> None:
        """1. Verify model path configuration resolves relative paths against project root."""
        adapter = FasterWhisperSTTAdapter(model_path="models/custom-model")
        expected = str(settings.project_root / "models" / "custom-model")
        self.assertEqual(adapter.model_path, expected)

    def test_lazy_model_loading(self) -> None:
        """2. Verify model is NOT loaded during adapter instantiation."""
        with patch("faster_whisper.WhisperModel") as mock_wm:
            adapter = FasterWhisperSTTAdapter(model_path="large-v3", device="cpu")
            mock_wm.assert_not_called()
            self.assertIsNone(adapter._whisper_model)

            # Accessing model triggers loading
            adapter._get_model()
            mock_wm.assert_called_once()

    def test_model_reused_across_transcriptions(self) -> None:
        """3. Verify model instance is cached and reused across multiple transcriptions."""
        mock_engine = MockWhisperModelEngine(text="Hello")
        adapter = FasterWhisperSTTAdapter(whisper_model_instance=mock_engine)

        async def run() -> None:
            chunk = AudioChunk(payload=b"RIFF_AUDIO_CHUNK_PAYLOAD_1")
            fmt = AudioFormat()

            res1 = await adapter.transcribe_detailed(chunk, fmt)
            res2 = await adapter.transcribe_detailed(chunk, fmt)

            self.assertEqual(mock_engine.call_count, 2)
            self.assertEqual(res1.text, "Hello")
            self.assertEqual(res2.text, "Hello")

        asyncio.run(run())

    def test_explicit_english_language_normalization(self) -> None:
        """4. Verify explicit English language normalization (en-IN -> en, en -> en)."""
        self.assertEqual(normalize_faster_whisper_input_language("en-IN"), "en")
        self.assertEqual(normalize_faster_whisper_input_language("en"), "en")

    def test_explicit_telugu_language_normalization(self) -> None:
        """5. Verify explicit Telugu language normalization (te-IN -> te, te -> te)."""
        self.assertEqual(normalize_faster_whisper_input_language("te-IN"), "te")
        self.assertEqual(normalize_faster_whisper_input_language("te"), "te")

    def test_auto_language_detection(self) -> None:
        """6. Verify auto language detection passes language=None to faster-whisper."""
        self.assertIsNone(normalize_faster_whisper_input_language("auto"))
        self.assertIsNone(normalize_faster_whisper_input_language(""))
        self.assertIsNone(normalize_faster_whisper_input_language(None))

    def test_transcription_parameters_task_beam_temperature(self) -> None:
        """7, 8, 9. Verify task='transcribe', beam_size=5, temperature=0 passed to engine."""
        mock_engine = MockWhisperModelEngine(text="Test speech")
        adapter = FasterWhisperSTTAdapter(whisper_model_instance=mock_engine)

        async def run() -> None:
            chunk = AudioChunk(payload=b"RIFF_TEST_AUDIO_BYTES")
            fmt = AudioFormat()
            await adapter.transcribe_detailed(chunk, fmt, language="te-IN")

            kwargs = mock_engine.last_transcribe_kwargs
            self.assertEqual(kwargs["language"], "te")
            self.assertEqual(kwargs["task"], "transcribe")
            self.assertEqual(kwargs["beam_size"], 5)
            self.assertEqual(kwargs["temperature"], 0.0)

        asyncio.run(run())

    def test_model_not_found_error(self) -> None:
        """10. Verify non-existent model directory path raises MODEL_NOT_FOUND error."""
        non_existent = str(settings.project_root / "models" / "non_existent_whisper_dir")
        adapter = FasterWhisperSTTAdapter(model_path=non_existent)

        with self.assertRaises(STTProviderError) as cm:
            adapter._get_model()

        self.assertEqual(cm.exception.code, "MODEL_NOT_FOUND")
        self.assertIn("model directory not found", cm.exception.message)

    def test_model_load_failure(self) -> None:
        """11. Verify model initialization failure raises structured MODEL_LOAD_FAILED error."""
        adapter = FasterWhisperSTTAdapter(model_path="large-v3", device="cpu")

        with patch("faster_whisper.WhisperModel", side_effect=Exception("Failed to find model path")):
            with self.assertRaises(STTProviderError) as cm:
                adapter._get_model()

            self.assertEqual(cm.exception.code, "MODEL_LOAD_FAILED")
            self.assertIn("model loading failed", cm.exception.message)

    def test_transcription_failure(self) -> None:
        """12. Verify engine transcription exception raises TRANSCRIPTION_FAILED error."""
        failing_engine = FailingMockEngine(Exception("Corrupted audio frame"))
        adapter = FasterWhisperSTTAdapter(whisper_model_instance=failing_engine)

        async def run() -> None:
            chunk = AudioChunk(payload=b"RIFF_CORRUPTED_BYTES")
            fmt = AudioFormat()
            with self.assertRaises(STTProviderError) as cm:
                await adapter.transcribe_detailed(chunk, fmt)

            self.assertEqual(cm.exception.code, "TRANSCRIPTION_FAILED")
            self.assertIn("faster-whisper transcription failed", cm.exception.message)

        asyncio.run(run())

    def test_provider_independent_result_mapping(self) -> None:
        """13. Verify transcription result maps cleanly to WhisperTranscriptionResult DTO."""
        mock_engine = MockWhisperModelEngine(text="హేలో నాకు మీ ప్రోడుక్స్ నీరే ఇంట్రేస్టుంది", language="te")
        adapter = FasterWhisperSTTAdapter(whisper_model_instance=mock_engine)

        async def run() -> None:
            chunk = AudioChunk(payload=b"RIFF_AUDIO_DATA_PAYLOAD")
            fmt = AudioFormat(sample_rate=16000)

            res = await adapter.transcribe_detailed(chunk, fmt, language="auto")
            self.assertIsInstance(res, WhisperTranscriptionResult)
            self.assertEqual(res.text, "హేలో నాకు మీ ప్రోడుక్స్ నీరే ఇంట్రేస్టుంది")
            self.assertEqual(res.language, "te-IN")
            self.assertEqual(res.confidence, 0.98)

        asyncio.run(run())

    def test_no_raw_faster_whisper_exceptions_leak(self) -> None:
        """14. Verify raw vendor exceptions are caught and wrapped in STTProviderError."""
        failing_engine = FailingMockEngine(RuntimeError("CTranslate2 internal error"))
        adapter = FasterWhisperSTTAdapter(whisper_model_instance=failing_engine)

        async def run() -> None:
            chunk = AudioChunk(payload=b"RIFF_RAW_DATA")
            fmt = AudioFormat()
            try:
                await adapter.transcribe_detailed(chunk, fmt)
                self.fail("Expected STTProviderError")
            except Exception as exc:
                self.assertIsInstance(exc, STTProviderError)
                self.assertNotIsInstance(exc, RuntimeError)

        asyncio.run(run())

    def test_locale_mapping_helpers(self) -> None:
        """Verify map_whisper_language_to_locale helper."""
        self.assertEqual(map_whisper_language_to_locale("te"), "te-IN")
        self.assertEqual(map_whisper_language_to_locale("en"), "en-IN")
        self.assertEqual(map_whisper_language_to_locale(""), settings.default_language)


if __name__ == "__main__":
    unittest.main()
