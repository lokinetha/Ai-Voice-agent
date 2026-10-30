"""
SQLAlchemy 2.x Repository Implementation for VoiceSession Aggregate Root.
"""

from __future__ import annotations

from datetime import UTC

from shared.kernel.specification import Specification
from shared.kernel.value_objects import (
    AgentId,
    ConversationId,
    EntityId,
    Timestamp,
    WorkspaceId,
)
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from voice.domain.entities.audio_stream import AudioStream
from voice.domain.entities.voice_participant import VoiceParticipant
from voice.domain.entities.voice_session import VoiceSession
from voice.domain.entities.voice_turn import VoiceTurn
from voice.domain.repositories.voice_session_repository import (
    VoiceSessionRepository,
)
from voice.domain.value_objects.audio_format import AudioFormat
from voice.domain.value_objects.speech_confidence import SpeechConfidence
from voice.domain.value_objects.voice_provider import VoiceProvider
from voice.domain.value_objects.voice_session_metrics import (
    VoiceSessionMetrics,
)
from voice.domain.value_objects.voice_session_status import (
    VoiceSessionStatus,
    VoiceSessionStatusType,
)
from voice.infrastructure.persistence.models import (
    AudioStreamModel,
    VoiceParticipantModel,
    VoiceSessionModel,
    VoiceTurnModel,
)


class SqlAlchemyVoiceSessionRepository(VoiceSessionRepository):
    """SQLAlchemy implementation of VoiceSessionRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: EntityId) -> VoiceSession | None:
        """Retrieve VoiceSession aggregate by ID."""
        stmt = select(VoiceSessionModel).where(VoiceSessionModel.id == str(id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[VoiceSession]:
        """Find all VoiceSessions in target Workspace."""
        stmt = select(VoiceSessionModel).where(
            VoiceSessionModel.workspace_id == str(workspace_id.value)
        )
        result = await self._session.execute(stmt)
        return [self._to_aggregate(m) for m in result.scalars().all()]

    async def find_by_conversation(self, conversation_id: ConversationId) -> list[VoiceSession]:
        """Find all VoiceSessions associated with target Conversation."""
        stmt = select(VoiceSessionModel).where(
            VoiceSessionModel.conversation_id == str(conversation_id.value)
        )
        result = await self._session.execute(stmt)
        return [self._to_aggregate(m) for m in result.scalars().all()]

    async def find_active_by_agent(self, agent_id: AgentId) -> list[VoiceSession]:
        """Find active VoiceSessions for target Agent."""
        stmt = select(VoiceSessionModel).where(
            VoiceSessionModel.agent_id == str(agent_id.value),
            VoiceSessionModel.status == "ACTIVE",
        )
        result = await self._session.execute(stmt)
        return [self._to_aggregate(m) for m in result.scalars().all()]

    async def save(self, aggregate: VoiceSession) -> None:
        """Persist or update VoiceSession aggregate root."""
        stmt = select(VoiceSessionModel).where(
            VoiceSessionModel.id == str(aggregate.id.value)
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = self._to_model(aggregate)
            self._session.add(model)
        else:
            existing.status = aggregate.status.value.value
            existing.error_message = aggregate.error_message
            existing.version = aggregate.version
            if aggregate.metrics is not None:
                existing.metrics_json = {
                    "total_turns": aggregate.metrics.total_turns,
                    "audio_duration_seconds": aggregate.metrics.audio_duration_seconds,
                    "average_latency_ms": aggregate.metrics.average_latency_ms,
                    "stt_latency_ms": aggregate.metrics.stt_latency_ms,
                    "tts_latency_ms": aggregate.metrics.tts_latency_ms,
                }

            # Update turns
            for t in aggregate.turns:
                turn_stmt = select(VoiceTurnModel).where(
                    VoiceTurnModel.id == str(t.id.value)
                )
                turn_res = await self._session.execute(turn_stmt)
                existing_turn = turn_res.scalar_one_or_none()
                if existing_turn:
                    existing_turn.transcript = t.transcript
                    existing_turn.confidence = t.confidence.value
                    existing_turn.agent_response_text = t.agent_response_text
                    existing_turn.audio_synthesized = t.audio_synthesized
                    existing_turn.is_completed = t.is_completed

    async def delete(self, aggregate: VoiceSession) -> None:
        """Delete VoiceSession aggregate from persistence."""
        stmt = sql_delete(VoiceSessionModel).where(
            VoiceSessionModel.id == str(aggregate.id.value)
        )
        await self._session.execute(stmt)

    async def find(self, spec: Specification[VoiceSession]) -> list[VoiceSession]:
        """Find VoiceSession aggregates satisfying specification filter."""
        stmt = select(VoiceSessionModel)
        result = await self._session.execute(stmt)
        aggregates = [self._to_aggregate(m) for m in result.scalars().all()]
        return [a for a in aggregates if spec.is_satisfied_by(a)]

    async def count(self, spec: Specification[VoiceSession]) -> int:
        """Count VoiceSession aggregates satisfying specification filter."""
        return len(await self.find(spec))

    def _to_model(self, aggregate: VoiceSession) -> VoiceSessionModel:
        """Map domain VoiceSession to ORM VoiceSessionModel."""
        stt_json = {"provider_name": aggregate.stt_provider.provider_name, "config": aggregate.stt_provider.config}
        tts_json = {"provider_name": aggregate.tts_provider.provider_name, "config": aggregate.tts_provider.config}
        telephony_json = {
            "provider_name": aggregate.telephony_provider.provider_name,
            "config": aggregate.telephony_provider.config,
        }
        metrics_json = {
            "total_turns": aggregate.metrics.total_turns,
            "audio_duration_seconds": aggregate.metrics.audio_duration_seconds,
            "average_latency_ms": aggregate.metrics.average_latency_ms,
            "stt_latency_ms": aggregate.metrics.stt_latency_ms,
            "tts_latency_ms": aggregate.metrics.tts_latency_ms,
        }

        participants = [
            VoiceParticipantModel(
                id=str(p.id.value),
                session_id=str(aggregate.id.value),
                role=p.role,
                display_name=p.display_name,
                phone_number=p.phone_number,
                created_at=p.created_at.value,
            )
            for p in aggregate.participants
        ]

        streams = [
            AudioStreamModel(
                id=str(s.id.value),
                session_id=str(aggregate.id.value),
                stream_type=s.stream_type,
                audio_format_json={
                    "sample_rate": s.audio_format.sample_rate,
                    "channels": s.audio_format.channels,
                    "encoding": s.audio_format.encoding,
                    "container": s.audio_format.container,
                },
                is_active=s.is_active,
                chunks_processed=s.chunks_processed,
                total_bytes_processed=s.total_bytes_processed,
                created_at=s.created_at.value,
            )
            for s in aggregate.streams
        ]

        turns = [
            VoiceTurnModel(
                id=str(t.id.value),
                session_id=str(aggregate.id.value),
                speaker_role=t.speaker_role,
                turn_number=t.turn_number,
                transcript=t.transcript,
                confidence=t.confidence.value,
                agent_response_text=t.agent_response_text,
                audio_synthesized=t.audio_synthesized,
                is_completed=t.is_completed,
                created_at=t.created_at.value,
            )
            for t in aggregate.turns
        ]

        return VoiceSessionModel(
            id=str(aggregate.id.value),
            workspace_id=str(aggregate.workspace_id.value),
            agent_id=str(aggregate.agent_id.value),
            conversation_id=str(aggregate.conversation_id.value),
            status=aggregate.status.value.value,
            error_message=aggregate.error_message,
            stt_provider_json=stt_json,
            tts_provider_json=tts_json,
            telephony_provider_json=telephony_json,
            metrics_json=metrics_json,
            version=aggregate.version,
            created_at=aggregate.created_at.value,
            participants=participants,
            streams=streams,
            turns=turns,
        )

    @staticmethod
    def _to_aggregate(model: VoiceSessionModel) -> VoiceSession:
        """Map ORM VoiceSessionModel to domain VoiceSession aggregate root."""
        created_at_dt = model.created_at
        if created_at_dt and created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=UTC)

        stt = VoiceProvider(
            provider_name=model.stt_provider_json.get("provider_name", "fake_stt") if model.stt_provider_json else "fake_stt",
            config=model.stt_provider_json.get("config", {}) if model.stt_provider_json else {},
        )
        tts = VoiceProvider(
            provider_name=model.tts_provider_json.get("provider_name", "fake_tts") if model.tts_provider_json else "fake_tts",
            config=model.tts_provider_json.get("config", {}) if model.tts_provider_json else {},
        )
        telephony = VoiceProvider(
            provider_name=model.telephony_provider_json.get("provider_name", "fake_telephony") if model.telephony_provider_json else "fake_telephony",
            config=model.telephony_provider_json.get("config", {}) if model.telephony_provider_json else {},
        )

        metrics = VoiceSessionMetrics()
        if model.metrics_json:
            metrics = VoiceSessionMetrics(
                total_turns=model.metrics_json.get("total_turns", 0),
                audio_duration_seconds=model.metrics_json.get("audio_duration_seconds", 0.0),
                average_latency_ms=model.metrics_json.get("average_latency_ms", 0.0),
                stt_latency_ms=model.metrics_json.get("stt_latency_ms", 0.0),
                tts_latency_ms=model.metrics_json.get("tts_latency_ms", 0.0),
            )

        participants = []
        for p in model.participants:
            p_created = p.created_at
            if p_created and p_created.tzinfo is None:
                p_created = p_created.replace(tzinfo=UTC)
            participants.append(
                VoiceParticipant(
                    id=EntityId(p.id),
                    role=p.role,
                    display_name=p.display_name,
                    phone_number=p.phone_number,
                    created_at=Timestamp(p_created),
                )
            )

        streams = []
        for s in model.streams:
            s_created = s.created_at
            if s_created and s_created.tzinfo is None:
                s_created = s_created.replace(tzinfo=UTC)
            fmt = AudioFormat()
            if s.audio_format_json:
                fmt = AudioFormat(
                    sample_rate=s.audio_format_json.get("sample_rate", 16000),
                    channels=s.audio_format_json.get("channels", 1),
                    encoding=s.audio_format_json.get("encoding", "pcm_s16le"),
                    container=s.audio_format_json.get("container", "raw"),
                )
            streams.append(
                AudioStream(
                    id=EntityId(s.id),
                    stream_type=s.stream_type,
                    audio_format=fmt,
                    is_active=s.is_active,
                    chunks_processed=s.chunks_processed,
                    total_bytes_processed=s.total_bytes_processed,
                    created_at=Timestamp(s_created),
                )
            )

        turns = []
        for t in model.turns:
            t_created = t.created_at
            if t_created and t_created.tzinfo is None:
                t_created = t_created.replace(tzinfo=UTC)
            turns.append(
                VoiceTurn(
                    id=EntityId(t.id),
                    speaker_role=t.speaker_role,
                    turn_number=t.turn_number,
                    transcript=t.transcript,
                    confidence=SpeechConfidence(t.confidence),
                    agent_response_text=t.agent_response_text,
                    audio_synthesized=t.audio_synthesized,
                    is_completed=t.is_completed,
                    created_at=Timestamp(t_created),
                )
            )

        return VoiceSession(
            id=EntityId(model.id),
            workspace_id=WorkspaceId(model.workspace_id),
            agent_id=AgentId(model.agent_id),
            conversation_id=ConversationId(model.conversation_id),
            status=VoiceSessionStatus(VoiceSessionStatusType(model.status)),
            stt_provider=stt,
            tts_provider=tts,
            telephony_provider=telephony,
            participants=participants,
            streams=streams,
            turns=turns,
            metrics=metrics,
            error_message=model.error_message,
            created_at=Timestamp(created_at_dt),
            version=model.version,
        )
