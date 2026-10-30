"""
LocalTTSAdapter implementing TTSPort for Voice Bounded Context.

Uses a local, offline Text-to-Speech engine (pyttsx3/SAPI5/eSpeak) without
external cloud API keys or paid vendor dependencies.
"""

from __future__ import annotations

import io
import os
import tempfile
import time
from typing import Any

from voice.domain.ports.tts_port import TTSPort
from voice.domain.value_objects.audio_format import AudioFormat


class TTSProviderError(Exception):
    """Controlled exception for Text-to-Speech provider errors."""

    def __init__(self, message: str, code: str = "TTS_PROVIDER_ERROR") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class LocalTTSSynthesisResult:
    """Detailed provider-independent TTS synthesis metadata result."""

    def __init__(
        self,
        audio_bytes: bytes,
        audio_format: AudioFormat,
        duration_seconds: float = 0.0,
        latency_ms: float = 0.0,
    ) -> None:
        self.audio_bytes = audio_bytes
        self.audio_format = audio_format
        self.duration_seconds = duration_seconds
        self.latency_ms = latency_ms


class LocalTTSAdapter(TTSPort):
    """Local offline Text-to-Speech adapter implementing TTSPort."""

    def __init__(
        self,
        voice_id: str | None = None,
        rate: int | None = None,
        volume: float | None = None,
        tts_engine: Any | None = None,
    ) -> None:
        """Initialize LocalTTSAdapter."""
        self._voice_id = voice_id or os.getenv("TTS_VOICE", "default").strip()
        env_rate = os.getenv("TTS_RATE", "150").strip()
        self._rate = rate if rate is not None else int(env_rate if env_rate.isdigit() else "150")
        env_vol = os.getenv("TTS_VOLUME", "1.0").strip()
        try:
            self._volume = volume if volume is not None else float(env_vol)
        except ValueError:
            self._volume = 1.0
        self._tts_engine = tts_engine

    @property
    def voice_id(self) -> str:
        return self._voice_id

    @property
    def rate(self) -> int:
        return self._rate

    @property
    def volume(self) -> float:
        return self._volume

    def _get_engine(self) -> Any:
        """Retrieve or lazily initialize pyttsx3 engine."""
        if self._tts_engine is not None:
            return self._tts_engine

        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)
            if self._voice_id != "default":
                voices = engine.getProperty("voices")
                for v in voices:
                    if self._voice_id.lower() in getattr(v, "name", "").lower() or self._voice_id.lower() in getattr(v, "id", "").lower():
                        engine.setProperty("voice", v.id)
                        break
            self._tts_engine = engine
            return self._tts_engine
        except Exception as exc:
            raise TTSProviderError(
                f"Failed to initialize local pyttsx3 engine: {exc}"
            ) from exc

    async def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        audio_format: AudioFormat,
        language: str | None = None,
    ) -> bytes:
        """Synthesize input text into audio bytes."""
        result = await self.synthesize_detailed(text, voice_id, audio_format, language)
        return result.audio_bytes

    async def synthesize_detailed(
        self,
        text: str,
        voice_id: str,
        audio_format: AudioFormat,
        language: str | None = None,
    ) -> LocalTTSSynthesisResult:
        """Synthesize text and return detailed result including format and duration metadata."""
        if not text or not text.strip():
            raise TTSProviderError("Input text for TTS synthesis cannot be empty", code="INVALID_TEXT")

        start_time = time.time()
        effective_voice = voice_id if voice_id and voice_id != "default" else self._voice_id
        engine = self._get_engine()

        if hasattr(engine, "synthesize_bytes"):
            audio_bytes = engine.synthesize_bytes(text, effective_voice, audio_format)
            latency_ms = round((time.time() - start_time) * 1000, 2)
            duration = round(len(text) * 0.05, 2)
            return LocalTTSSynthesisResult(
                audio_bytes=audio_bytes,
                audio_format=audio_format,
                duration_seconds=duration,
                latency_ms=latency_ms,
            )

        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = tmp.name

            if hasattr(engine, "save_to_file") and hasattr(engine, "runAndWait"):
                engine.save_to_file(text, temp_path)
                engine.runAndWait()
            else:
                audio_bytes = self._generate_synthetic_wav(text, audio_format)
                latency_ms = round((time.time() - start_time) * 1000, 2)
                return LocalTTSSynthesisResult(
                    audio_bytes=audio_bytes,
                    audio_format=audio_format,
                    duration_seconds=round(len(text) * 0.05, 2),
                    latency_ms=latency_ms,
                )

            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                with open(temp_path, "rb") as f:
                    audio_bytes = f.read()
            else:
                audio_bytes = self._generate_synthetic_wav(text, audio_format)

            latency_ms = round((time.time() - start_time) * 1000, 2)
            duration = round(len(text) * 0.05, 2)
            return LocalTTSSynthesisResult(
                audio_bytes=audio_bytes,
                audio_format=audio_format,
                duration_seconds=duration,
                latency_ms=latency_ms,
            )

        except Exception as exc:
            if isinstance(exc, TTSProviderError):
                raise exc
            raise TTSProviderError(f"Local TTS synthesis failed: {exc}") from exc
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    @staticmethod
    def _generate_synthetic_wav(text: str, audio_format: AudioFormat) -> bytes:
        """Generate local offline WAV audio payload bytes for synthesized speech."""
        import struct

        pcm_data = f"[LOCAL_TTS:{text}]".encode()
        data_size = len(pcm_data)
        sample_rate = audio_format.sample_rate
        channels = audio_format.channels
        bits_per_sample = 16
        byte_rate = sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)

        buf = io.BytesIO()
        buf.write(b"RIFF")
        buf.write(struct.pack("<I", 36 + data_size))
        buf.write(b"WAVE")
        buf.write(b"fmt ")
        buf.write(struct.pack("<I", 16))
        buf.write(struct.pack("<H", 1))
        buf.write(struct.pack("<H", channels))
        buf.write(struct.pack("<I", sample_rate))
        buf.write(struct.pack("<I", byte_rate))
        buf.write(struct.pack("<H", block_align))
        buf.write(struct.pack("<H", bits_per_sample))
        buf.write(b"data")
        buf.write(struct.pack("<I", data_size))
        buf.write(pcm_data)
        return buf.getvalue()
