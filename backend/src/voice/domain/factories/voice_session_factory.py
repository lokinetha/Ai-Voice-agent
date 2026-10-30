"""
VoiceSessionFactory for Voice Bounded Context.

Encapsulates construction of new VoiceSession Aggregate Roots.
"""

from __future__ import annotations

from shared.kernel.value_objects import (
    AgentId,
    ConversationId,
    EntityId,
    WorkspaceId,
)

from voice.domain.entities.audio_stream import AudioStream
from voice.domain.entities.voice_participant import VoiceParticipant
from voice.domain.entities.voice_session import VoiceSession
from voice.domain.value_objects.audio_format import AudioFormat
from voice.domain.value_objects.voice_provider import VoiceProvider


class VoiceSessionFactory:
    """Factory constructing new VoiceSession Aggregate Roots."""

    @classmethod
    def create(
        cls,
        workspace_id: WorkspaceId,
        agent_id: AgentId,
        conversation_id: ConversationId,
        stt_provider: VoiceProvider | None = None,
        tts_provider: VoiceProvider | None = None,
        telephony_provider: VoiceProvider | None = None,
        audio_format: AudioFormat | None = None,
        session_id: EntityId | None = None,
    ) -> VoiceSession:
        """Create and initialize a new VoiceSession aggregate root with stream channels and participants.

        Args:
            workspace_id: Owning WorkspaceId.
            agent_id: Target AgentId.
            conversation_id: Target ConversationId.
            stt_provider: STT Provider configuration.
            tts_provider: TTS Provider configuration.
            telephony_provider: Telephony Provider configuration.
            audio_format: Stream AudioFormat.
            session_id: Optional explicit session EntityId.

        Returns:
            Initialized VoiceSession aggregate root.
        """
        id_val = session_id or EntityId()
        fmt = audio_format or AudioFormat()

        participants = [
            VoiceParticipant(id=EntityId(), role="USER", display_name="Caller"),
            VoiceParticipant(id=EntityId(), role="AGENT", display_name="AI Agent"),
        ]

        streams = [
            AudioStream(
                id=EntityId(),
                stream_type="INBOUND",
                audio_format=fmt,
            ),
            AudioStream(
                id=EntityId(),
                stream_type="OUTBOUND",
                audio_format=fmt,
            ),
        ]

        session = VoiceSession(
            id=id_val,
            workspace_id=workspace_id,
            agent_id=agent_id,
            conversation_id=conversation_id,
            stt_provider=stt_provider or VoiceProvider("fake_stt"),
            tts_provider=tts_provider or VoiceProvider("fake_tts"),
            telephony_provider=telephony_provider or VoiceProvider("fake_telephony"),
            participants=participants,
            streams=streams,
        )

        return session
