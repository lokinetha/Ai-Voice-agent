"""
PiperTTSAdapter implementing TTSPort for Voice Bounded Context.

Uses local Piper TTS ONNX neural models for fast, high-quality offline speech synthesis
across multiple languages (English, Telugu) without external cloud API keys.
"""

from __future__ import annotations

import io
import os
import time
import wave
from pathlib import Path
from typing import Any

from shared.config.settings import settings

from voice.domain.ports.tts_port import TTSPort
from voice.domain.value_objects.audio_format import AudioFormat
from voice.infrastructure.adapters.local_tts_adapter import (
    LocalTTSSynthesisResult,
    TTSProviderError,
)


def create_pcm_wav_bytes(
    pcm_data: bytes,
    sample_rate: int = 22050,
    channels: int = 1,
    sample_width: int = 2,
) -> bytes:
    """Helper utility generating valid PCM WAV byte payload."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return buffer.getvalue()


class PiperTTSAdapter(TTSPort):
    """Local Piper ONNX neural Text-to-Speech adapter supporting multilingual models."""

    def __init__(
        self,
        model_path: str | None = None,
        config_path: str | None = None,
        device: str | None = None,
        length_scale: float | None = None,
        noise_scale: float | None = None,
        noise_w_scale: float | None = None,
        piper_engine: Any | None = None,
    ) -> None:
        """Initialize PiperTTSAdapter."""
        raw_model = (
            model_path
            if model_path is not None and model_path.strip() != ""
            else settings.piper_en_model_path
        )
        raw_config = (
            config_path
            if config_path is not None and config_path.strip() != ""
            else settings.piper_en_config_path
        )

        if raw_model:
            model_obj = Path(raw_model)
            if not model_obj.is_absolute():
                model_obj = settings.project_root / model_obj
            self._model_path = str(model_obj)
        else:
            self._model_path = ""

        if raw_config:
            config_obj = Path(raw_config)
            if not config_obj.is_absolute():
                config_obj = settings.project_root / config_obj
            self._config_path = str(config_obj)
        else:
            self._config_path = ""

        self._device = device if device is not None else settings.piper_device
        self._length_scale = (
            length_scale if length_scale is not None else settings.piper_length_scale
        )
        self._noise_scale = (
            noise_scale if noise_scale is not None else settings.piper_noise_scale
        )
        self._noise_w_scale = (
            noise_w_scale
            if noise_w_scale is not None
            else settings.piper_noise_w_scale
        )
        self._piper_engine = piper_engine
        self._loaded_engines: dict[str, Any] = {}

    @property
    def model_path(self) -> str:
        return self._model_path

    @property
    def config_path(self) -> str:
        return self._config_path

    @property
    def device(self) -> str:
        return self._device

    def get_model_path_for_language(self, language: str | None) -> str:
        """Resolve Piper ONNX model file path for the requested language code."""
        if not language:
            return self._model_path or settings.piper_en_model_path

        lang_code = language.strip().lower()
        if lang_code.startswith("te"):
            te_path = settings.piper_te_model_path
            if not te_path or not os.path.exists(te_path):
                raise TTSProviderError(
                    f"Piper TTS model file for language '{language}' ('te') is not configured or missing on disk",
                    code="MODEL_NOT_FOUND",
                )
            return te_path

        if lang_code.startswith("en"):
            en_path = self._model_path or settings.piper_en_model_path
            if not en_path or not os.path.exists(en_path):
                raise TTSProviderError(
                    f"Piper TTS model file for language '{language}' ('en') is not configured or missing on disk",
                    code="MODEL_NOT_FOUND",
                )
            return en_path

        return self._model_path or settings.piper_en_model_path

    def _get_voice_engine(self, language: str | None = None) -> Any:
        """Retrieve or lazily initialize the PiperVoice model instance for language."""
        if self._piper_engine is not None:
            return self._piper_engine

        target_path = self.get_model_path_for_language(language)

        if not target_path or not os.path.exists(target_path):
            lang_str = language or "en"
            raise TTSProviderError(
                f"Piper TTS model file for language '{lang_str}' not found at path: '{target_path}'",
                code="MODEL_NOT_FOUND",
            )

        if target_path in self._loaded_engines:
            return self._loaded_engines[target_path]

        try:
            from piper import PiperVoice

            config_file = f"{target_path}.json"
            use_cuda = self._device.lower() == "cuda"
            engine = PiperVoice.load(
                target_path,
                config_path=config_file if os.path.exists(config_file) else None,
                use_cuda=use_cuda,
            )
            self._loaded_engines[target_path] = engine
            return engine
        except Exception as exc:
            if isinstance(exc, TTSProviderError):
                raise exc
            raise TTSProviderError(
                f"Failed to load Piper TTS model from '{target_path}': {exc}",
                code="MODEL_LOAD_FAILED",
            ) from exc

    async def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        audio_format: AudioFormat,
        language: str | None = None,
    ) -> bytes:
        """Synthesize text string into speech WAV audio bytes."""
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
            raise TTSProviderError(
                "Input text for Piper TTS synthesis cannot be empty",
                code="INVALID_TEXT",
            )

        start_time = time.time()
        engine = self._get_voice_engine(language)

        # 1. Handle mock engine in unit tests
        if hasattr(engine, "synthesize_bytes"):
            raw_data = engine.synthesize_bytes(text, voice_id, audio_format)
            try:
                with wave.open(io.BytesIO(raw_data), "rb") as wf:
                    duration = round(wf.getnframes() / float(wf.getframerate()), 2)
                audio_bytes = raw_data
            except Exception:
                audio_bytes = create_pcm_wav_bytes(
                    raw_data,
                    sample_rate=audio_format.sample_rate or 22050,
                    channels=1,
                    sample_width=2,
                )
                duration = round(len(text) * 0.05, 2)

            latency_ms = round((time.time() - start_time) * 1000, 2)
            return LocalTTSSynthesisResult(
                audio_bytes=audio_bytes,
                audio_format=audio_format,
                duration_seconds=duration,
                latency_ms=latency_ms,
            )

        # 2. Real Piper Voice synthesis into WAV stream
        try:
            from piper.config import SynthesisConfig

            syn_config = SynthesisConfig(
                length_scale=self._length_scale,
                noise_scale=self._noise_scale,
                noise_w_scale=self._noise_w_scale,
            )

            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wav_file:
                if hasattr(engine, "synthesize_wav"):
                    engine.synthesize_wav(text, wav_file, syn_config=syn_config)
                elif hasattr(engine, "synthesize"):
                    sample_rate = getattr(
                        getattr(engine, "config", None),
                        "sample_rate",
                        audio_format.sample_rate or 22050,
                    )
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    for chunk in engine.synthesize(text, syn_config=syn_config):
                        pcm_bytes = getattr(chunk, "audio_int16_bytes", getattr(chunk, "audio_bytes", b""))
                        if pcm_bytes:
                            wav_file.writeframes(pcm_bytes)
                else:
                    raise TTSProviderError(
                        "Loaded Piper engine lacks synthesis methods",
                        code="SYNTHESIS_FAILED",
                    )

            audio_bytes = buffer.getvalue()

            if not audio_bytes or len(audio_bytes) <= 44:
                raise TTSProviderError(
                    "Piper TTS produced an empty or invalid WAV output",
                    code="SYNTHESIS_FAILED",
                )

            # Validate generated WAV header and compute duration
            try:
                with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                    num_frames = wf.getnframes()
                    frame_rate = wf.getframerate()
                    duration = round(num_frames / float(frame_rate), 2) if frame_rate > 0 else 0.0
            except wave.Error as err:
                raise TTSProviderError(
                    f"Generated WAV file header is invalid: {err}",
                    code="INVALID_WAV_HEADER",
                ) from err

            latency_ms = round((time.time() - start_time) * 1000, 2)
            return LocalTTSSynthesisResult(
                audio_bytes=audio_bytes,
                audio_format=audio_format,
                duration_seconds=duration,
                latency_ms=latency_ms,
            )

        except Exception as exc:
            if isinstance(exc, TTSProviderError):
                raise exc
            raise TTSProviderError(
                f"Piper TTS synthesis failed: {exc}", code="SYNTHESIS_FAILED"
            ) from exc
