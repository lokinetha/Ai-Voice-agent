"""
VoiceAgentPipeline Application Orchestrator for End-to-End Voice Turns.

Orchestrates Multilingual STT -> Conversation -> AgentRuntimeService (Gemini + Prompt + Knowledge)
-> Conversation -> Multilingual TTS -> Output Audio File.
"""

from __future__ import annotations

import logging
import os
import time

from agent_runtime.application.services.agent_runtime_service import (
    AgentRuntimeService,
)
from shared.config.settings import settings
from shared.kernel.result import Error, Result

from voice.application.dto.voice_pipeline_dto import (
    VoiceTurnInput,
    VoiceTurnResult,
)
from voice.domain.ports.conversation_port import ConversationPort
from voice.domain.ports.stt_port import STTPort
from voice.domain.ports.tts_port import TTSPort
from voice.domain.value_objects.audio_chunk import AudioChunk
from voice.domain.value_objects.audio_format import AudioFormat
from voice.infrastructure.adapters.local_tts_adapter import TTSProviderError
from voice.infrastructure.adapters.local_whisper_stt_adapter import (
    STTProviderError,
    is_telugu_text,
)

logger = logging.getLogger(__name__)


class VoiceAgentPipeline:
    """End-to-End Multilingual Voice Agent Pipeline Orchestrator."""

    def __init__(
        self,
        stt_port: STTPort,
        agent_runtime_service: AgentRuntimeService,
        tts_port: TTSPort,
        conversation_port: ConversationPort,
    ) -> None:
        self._stt_port = stt_port
        self._runtime_service = agent_runtime_service
        self._tts_port = tts_port
        self._conv_port = conversation_port

    async def execute_voice_turn(
        self, turn_input: VoiceTurnInput
    ) -> Result[VoiceTurnResult]:
        """Execute complete end-to-end multilingual voice turn pipeline."""
        start_time = time.time()
        corr_id = (
            turn_input.correlation_id
            or f"{turn_input.workspace_id}:{turn_input.conversation_id}"
        )

        # Step 1: Read audio input payload
        payload_bytes = turn_input.audio_bytes
        if turn_input.audio_file_path:
            if not os.path.exists(turn_input.audio_file_path):
                return Result.fail(
                    Error(
                        "FILE_NOT_FOUND",
                        f"Input audio file not found: {turn_input.audio_file_path}",
                    )
                )
            try:
                with open(turn_input.audio_file_path, "rb") as f:
                    payload_bytes = f.read()
            except OSError as err:
                return Result.fail(
                    Error("READ_ERROR", f"Failed to read input audio file: {err}")
                )

        if not payload_bytes:
            return Result.fail(
                Error("INVALID_AUDIO", "Input audio payload cannot be empty")
            )

        # Step 2: Speech-to-Text Transcription with Language Detection
        stt_start = time.time()
        fmt = AudioFormat(sample_rate=16000)
        chunk = AudioChunk(payload=payload_bytes)
        req_lang = turn_input.language or settings.whisper_language

        try:
            if hasattr(self._stt_port, "transcribe_detailed"):
                res_detailed = await self._stt_port.transcribe_detailed(
                    chunk, fmt, language=req_lang
                )
                transcript = res_detailed.text
                detected_lang = res_detailed.language or settings.default_language
            else:
                transcript, _confidence = await self._stt_port.transcribe_audio_chunk(
                    chunk, fmt, language=req_lang
                )
                detected_lang = (
                    req_lang
                    if (req_lang and req_lang != "auto")
                    else settings.default_language
                )
        except STTProviderError as err:
            return Result.fail(
                Error("STT_FAILURE", f"Speech-to-Text transcription failed: {err.message}")
            )
        except Exception as err:
            return Result.fail(
                Error("STT_FAILURE", f"Speech-to-Text transcription failed: {err}")
            )

        stt_latency = round((time.time() - stt_start) * 1000, 2)

        if not transcript or not transcript.strip():
            return Result.fail(
                Error("STT_EMPTY_TRANSCRIPT", "STT transcribed empty speech")
            )

        # Step 3: Validate language against supported_languages
        normalized_lang = detected_lang.strip().lower()
        supported = [s.lower() for s in settings.supported_languages]
        is_supported = any(
            normalized_lang == supp or normalized_lang.startswith(supp.split("-")[0])
            for supp in supported
        )

        if not is_supported:
            return Result.fail(
                Error(
                    "UNSUPPORTED_LANGUAGE",
                    f"Language '{detected_lang}' is not supported. Supported languages: {settings.supported_languages}",
                )
            )

        # Step 4: Persist User Transcript in Conversation
        await self._conv_port.append_message_to_conversation(
            conversation_id=turn_input.conversation_id,
            role="CUSTOMER",
            content=transcript,
        )

        # Step 5: Agent Runtime Orchestration (Agent + Prompt + Context + Knowledge + Gemini LLM)
        llm_start = time.time()
        runtime_res = await self._runtime_service.execute_turn(
            workspace_id=turn_input.workspace_id,
            agent_id=turn_input.agent_id,
            conversation_id=turn_input.conversation_id,
            message_text=transcript,
            correlation_id=corr_id,
            language=detected_lang,
        )

        if runtime_res.is_failure:
            return Result.fail(
                Error(
                    "AGENT_RUNTIME_FAILURE",
                    f"Agent runtime execution failed: {runtime_res.error.message}",
                )
            )

        agent_response = runtime_res.value
        agent_text = agent_response.content
        llm_latency = round((time.time() - llm_start) * 1000, 2)

        # Step 5.1: Language Preservation Validation before TTS
        if normalized_lang.startswith("te") and agent_text.strip():
            if not is_telugu_text(agent_text):
                return Result.fail(
                    Error(
                        "LANGUAGE_MISMATCH",
                        f"Expected Telugu script response for language '{detected_lang}', but agent response was generated in non-Telugu text: '{agent_text[:60]}...'",
                    )
                )

        # Step 6: Text-to-Speech Synthesis for Language
        tts_start = time.time()
        try:
            audio_out_bytes = await self._tts_port.synthesize_speech(
                text=agent_text,
                voice_id=turn_input.voice_id,
                audio_format=fmt,
                language=detected_lang,
            )
        except TTSProviderError as err:
            return Result.fail(
                Error("TTS_FAILURE", f"Text-to-Speech synthesis failed: {err.message}")
            )
        except Exception as err:
            return Result.fail(
                Error("TTS_FAILURE", f"Text-to-Speech synthesis failed: {err}")
            )

        tts_latency = round((time.time() - tts_start) * 1000, 2)

        # Step 7: Write output audio file if configured and payload is valid audio
        output_path = turn_input.output_audio_path
        if output_path:
            # Enforce rule: Never write textual fake TTS output into .wav files
            is_wav_file = output_path.lower().endswith(".wav")
            is_real_wav_bytes = audio_out_bytes.startswith(b"RIFF")

            if is_wav_file and not is_real_wav_bytes:
                logger.warning(
                    "Skipping writing non-WAV TTS payload (%d bytes, starts with %r) to .wav file '%s'",
                    len(audio_out_bytes),
                    audio_out_bytes[:10],
                    output_path,
                )
            else:
                try:
                    parent_dir = os.path.dirname(output_path)
                    if parent_dir and not os.path.exists(parent_dir):
                        os.makedirs(parent_dir, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(audio_out_bytes)
                except OSError as err:
                    logger.warning("Failed to write output audio file to '%s': %s", output_path, err)

        total_latency = round((time.time() - start_time) * 1000, 2)

        return Result.ok(
            VoiceTurnResult(
                transcript=transcript,
                agent_response_text=agent_text,
                audio_bytes=audio_out_bytes,
                output_audio_path=output_path,
                workspace_id=turn_input.workspace_id,
                agent_id=turn_input.agent_id,
                conversation_id=turn_input.conversation_id,
                correlation_id=corr_id,
                detected_language=detected_lang,
                stt_latency_ms=stt_latency,
                llm_latency_ms=llm_latency,
                tts_latency_ms=tts_latency,
                total_latency_ms=total_latency,
            )
        )
