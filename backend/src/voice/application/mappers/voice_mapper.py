"""
VoiceMapper for mapping between Domain VoiceSession aggregate and DTOs.
"""

from __future__ import annotations

from voice.application.dto.voice_dto import (
    AudioFormatDTO,
    AudioStreamDTO,
    VoiceParticipantDTO,
    VoiceSessionDTO,
    VoiceSessionMetricsDTO,
    VoiceTurnDTO,
)
from voice.domain.entities.audio_stream import AudioStream
from voice.domain.entities.voice_participant import VoiceParticipant
from voice.domain.entities.voice_session import VoiceSession
from voice.domain.entities.voice_turn import VoiceTurn


class VoiceMapper:
    """Static mapper converting VoiceSession domain entities to DTOs."""

    @staticmethod
    def to_dto(session: VoiceSession) -> VoiceSessionDTO:
        """Map VoiceSession aggregate root to VoiceSessionDTO."""
        metrics_dto = None
        if session.metrics is not None:
            metrics_dto = VoiceSessionMetricsDTO(
                total_turns=session.metrics.total_turns,
                audio_duration_seconds=session.metrics.audio_duration_seconds,
                average_latency_ms=session.metrics.average_latency_ms,
                stt_latency_ms=session.metrics.stt_latency_ms,
                tts_latency_ms=session.metrics.tts_latency_ms,
            )

        participant_dtos = tuple(VoiceMapper.to_participant_dto(p) for p in session.participants)
        stream_dtos = tuple(VoiceMapper.to_stream_dto(s) for s in session.streams)
        turn_dtos = tuple(VoiceMapper.to_turn_dto(t) for t in session.turns)

        return VoiceSessionDTO(
            id=str(session.id.value),
            workspace_id=str(session.workspace_id.value),
            agent_id=str(session.agent_id.value),
            conversation_id=str(session.conversation_id.value),
            status=session.status.value.value,
            stt_provider_name=session.stt_provider.provider_name,
            tts_provider_name=session.tts_provider.provider_name,
            telephony_provider_name=session.telephony_provider.provider_name,
            participants=participant_dtos,
            streams=stream_dtos,
            turns=turn_dtos,
            metrics=metrics_dto,
            error_message=session.error_message,
            version=session.version,
            created_at=session.created_at.value,
        )

    @staticmethod
    def to_participant_dto(participant: VoiceParticipant) -> VoiceParticipantDTO:
        """Map VoiceParticipant entity to VoiceParticipantDTO."""
        return VoiceParticipantDTO(
            id=str(participant.id.value),
            role=participant.role,
            display_name=participant.display_name,
            phone_number=participant.phone_number,
        )

    @staticmethod
    def to_stream_dto(stream: AudioStream) -> AudioStreamDTO:
        """Map AudioStream entity to AudioStreamDTO."""
        fmt_dto = AudioFormatDTO(
            sample_rate=stream.audio_format.sample_rate,
            channels=stream.audio_format.channels,
            encoding=stream.audio_format.encoding,
            container=stream.audio_format.container,
        )
        return AudioStreamDTO(
            id=str(stream.id.value),
            stream_type=stream.stream_type,
            audio_format=fmt_dto,
            is_active=stream.is_active,
            chunks_processed=stream.chunks_processed,
            total_bytes_processed=stream.total_bytes_processed,
        )

    @staticmethod
    def to_turn_dto(turn: VoiceTurn) -> VoiceTurnDTO:
        """Map VoiceTurn entity to VoiceTurnDTO."""
        return VoiceTurnDTO(
            id=str(turn.id.value),
            speaker_role=turn.speaker_role,
            turn_number=turn.turn_number,
            transcript=turn.transcript,
            confidence=turn.confidence.value,
            agent_response_text=turn.agent_response_text,
            audio_synthesized=turn.audio_synthesized,
            is_completed=turn.is_completed,
        )
