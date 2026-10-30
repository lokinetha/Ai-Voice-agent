"""
Voice Bounded Context Dependency Injection Bootstrap.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shared.config.settings import load_env_file, resolve_llm_adapter, settings
from shared.kernel.unit_of_work import UnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from voice.application.commands.end_voice_session import (
    EndVoiceSessionHandler,
)
from voice.application.commands.generate_agent_response import (
    GenerateAgentResponseHandler,
)
from voice.application.commands.process_audio_chunk import (
    ProcessAudioChunkHandler,
)
from voice.application.commands.process_transcript import (
    ProcessTranscriptHandler,
)
from voice.application.commands.start_voice_session import (
    StartVoiceSessionHandler,
)
from voice.application.commands.synthesize_response import (
    SynthesizeResponseHandler,
)
from voice.application.queries.get_voice_session import (
    GetVoiceSessionHandler,
)
from voice.application.queries.get_voice_session_metrics import (
    GetVoiceSessionMetricsHandler,
)
from voice.application.services.multi_turn_voice_pipeline import (
    MultiTurnVoicePipeline,
)
from voice.application.services.voice_agent_pipeline import VoiceAgentPipeline
from voice.domain.ports.audio_stream_port import AudioStreamPort
from voice.domain.ports.conversation_port import ConversationPort
from voice.domain.ports.llm_runtime_port import LLMRuntimePort
from voice.domain.ports.stt_port import STTPort
from voice.domain.ports.telephony_port import TelephonyPort
from voice.domain.ports.tts_port import TTSPort
from voice.domain.repositories.voice_session_repository import (
    VoiceSessionRepository,
)
from voice.domain.services.voice_session_lifecycle_service import (
    VoiceSessionLifecycleService,
)
from voice.infrastructure.adapters.conversation_adapter import ConversationAdapter
from voice.infrastructure.adapters.fake_audio_stream_adapter import (
    FakeAudioStreamAdapter,
)
from voice.infrastructure.adapters.fake_stt_adapter import FakeSTTAdapter
from voice.infrastructure.adapters.fake_telephony_adapter import (
    FakeTelephonyAdapter,
)
from voice.infrastructure.adapters.fake_tts_adapter import FakeTTSAdapter
from voice.infrastructure.adapters.in_memory_conversation_adapter import (
    InMemoryConversationAdapter,
)
from voice.infrastructure.adapters.local_tts_adapter import LocalTTSAdapter
from voice.infrastructure.adapters.local_whisper_stt_adapter import (
    LocalWhisperSTTAdapter,
)
from voice.infrastructure.adapters.piper_tts_adapter import PiperTTSAdapter


class VoiceContainer:
    """Dependency Container for Voice Context services and handlers."""

    def __init__(
        self,
        session: AsyncSession | None = None,
        stt_port: STTPort | None = None,
        tts_port: TTSPort | None = None,
        telephony_port: TelephonyPort | None = None,
        stream_port: AudioStreamPort | None = None,
        llm_runtime_port: LLMRuntimePort | None = None,
        conversation_port: ConversationPort | None = None,
    ) -> None:
        load_env_file()
        self._session = session
        if session is not None:
            from identity.bootstrap.dependency_injection import SqlAlchemyUnitOfWork

            from voice.infrastructure.persistence.sqlalchemy_voice_session_repository import (
                SqlAlchemyVoiceSessionRepository,
            )

            self._session_repository: VoiceSessionRepository = SqlAlchemyVoiceSessionRepository(session)
            self._uow: UnitOfWork = SqlAlchemyUnitOfWork(session)
            self._conversation_port: ConversationPort = conversation_port or ConversationAdapter(session)
        else:
            self._session_repository = None  # type: ignore[assignment]
            self._uow = None  # type: ignore[assignment]
            self._conversation_port = conversation_port or InMemoryConversationAdapter()

        # STT Provider selection via Settings (fake | local | faster-whisper)
        stt_provider_type = (settings.stt_provider or "fake").lower()
        if stt_port is not None:
            self._stt_port = stt_port
        elif stt_provider_type in ("faster-whisper", "faster_whisper"):
            from voice.infrastructure.adapters.faster_whisper_stt_adapter import (
                FasterWhisperSTTAdapter,
            )

            self._stt_port = FasterWhisperSTTAdapter()
        elif stt_provider_type in ("local", "whisper"):
            self._stt_port = LocalWhisperSTTAdapter()
        else:
            self._stt_port = FakeSTTAdapter()

        # TTS Provider selection via Settings (fake | local | piper)
        tts_provider_type = (settings.tts_provider or "fake").lower()
        if tts_port is not None:
            self._tts_port = tts_port
        elif tts_provider_type == "piper":
            self._tts_port = PiperTTSAdapter()
        elif tts_provider_type == "local":
            self._tts_port = LocalTTSAdapter()
        else:
            self._tts_port = FakeTTSAdapter()

        self._telephony_port: TelephonyPort = telephony_port or FakeTelephonyAdapter()
        self._stream_port: AudioStreamPort = stream_port or FakeAudioStreamAdapter()

        # LLM Provider selection via Settings helper
        if llm_runtime_port is not None:
            self._llm_runtime_port = llm_runtime_port
        else:
            self._llm_runtime_port = resolve_llm_adapter(settings)

        self._lifecycle_service = VoiceSessionLifecycleService()

    @property
    def session_repository(self) -> VoiceSessionRepository:
        return self._session_repository

    @property
    def stt_port(self) -> STTPort:
        return self._stt_port

    @property
    def tts_port(self) -> TTSPort:
        return self._tts_port

    @property
    def telephony_port(self) -> TelephonyPort:
        return self._telephony_port

    @property
    def stream_port(self) -> AudioStreamPort:
        return self._stream_port

    @property
    def llm_runtime_port(self) -> LLMRuntimePort:
        return self._llm_runtime_port

    @property
    def conversation_port(self) -> ConversationPort:
        return self._conversation_port

    @property
    def lifecycle_service(self) -> VoiceSessionLifecycleService:
        return self._lifecycle_service

    @property
    def unit_of_work(self) -> UnitOfWork:
        return self._uow

    def create_single_turn_pipeline(
        self,
        agent_runtime_service: Any,
        conversation_port: ConversationPort | None = None,
    ) -> VoiceAgentPipeline:
        """Create VoiceAgentPipeline with container's configured STT and TTS ports."""
        conv_p = conversation_port or self._conversation_port
        return VoiceAgentPipeline(
            stt_port=self._stt_port,
            agent_runtime_service=agent_runtime_service,
            tts_port=self._tts_port,
            conversation_port=conv_p,
        )

    def create_multi_turn_pipeline(
        self,
        agent_runtime_service: Any,
        conversation_port: ConversationPort | None = None,
    ) -> MultiTurnVoicePipeline:
        """Create MultiTurnVoicePipeline with container's configured STT and TTS ports."""
        single_p = self.create_single_turn_pipeline(
            agent_runtime_service=agent_runtime_service,
            conversation_port=conversation_port,
        )
        return MultiTurnVoicePipeline(single_p)

    def get_start_voice_session_handler(self) -> StartVoiceSessionHandler:
        return StartVoiceSessionHandler(
            session_repository=self._session_repository,
            lifecycle_service=self._lifecycle_service,
            unit_of_work=self._uow,
        )

    def get_process_audio_chunk_handler(self) -> ProcessAudioChunkHandler:
        return ProcessAudioChunkHandler(
            session_repository=self._session_repository,
            stt_port=self._stt_port,
            unit_of_work=self._uow,
        )

    def get_process_transcript_handler(self) -> ProcessTranscriptHandler:
        return ProcessTranscriptHandler(
            session_repository=self._session_repository,
            conversation_port=self._conversation_port,
            unit_of_work=self._uow,
        )

    def get_generate_agent_response_handler(self) -> GenerateAgentResponseHandler:
        return GenerateAgentResponseHandler(
            session_repository=self._session_repository,
            llm_runtime_port=self._llm_runtime_port,
            conversation_port=self._conversation_port,
            unit_of_work=self._uow,
        )

    def get_synthesize_response_handler(self) -> SynthesizeResponseHandler:
        return SynthesizeResponseHandler(
            session_repository=self._session_repository,
            tts_port=self._tts_port,
            audio_stream_port=self._stream_port,
            unit_of_work=self._uow,
        )

    def get_end_voice_session_handler(self) -> EndVoiceSessionHandler:
        return EndVoiceSessionHandler(
            session_repository=self._session_repository,
            telephony_port=self._telephony_port,
            lifecycle_service=self._lifecycle_service,
            unit_of_work=self._uow,
        )

    def get_voice_session_handler(self) -> GetVoiceSessionHandler:
        return GetVoiceSessionHandler(session_repository=self._session_repository)

    def get_voice_session_metrics_handler(self) -> GetVoiceSessionMetricsHandler:
        return GetVoiceSessionMetricsHandler(session_repository=self._session_repository)
