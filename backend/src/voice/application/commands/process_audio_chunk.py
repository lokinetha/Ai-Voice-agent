"""
ProcessAudioChunk Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import EntityId

from voice.application.dto.voice_dto import VoiceSessionDTO
from voice.application.mappers.voice_mapper import VoiceMapper
from voice.domain.ports.stt_port import STTPort
from voice.domain.repositories.voice_session_repository import (
    VoiceSessionRepository,
)
from voice.domain.specifications.can_accept_audio_spec import (
    CanAcceptAudioSpec,
)
from voice.domain.value_objects.audio_chunk import AudioChunk


@dataclass(frozen=True)
class ProcessAudioChunkCommand(Command):
    """Command sending raw audio bytes chunk for real-time STT processing."""

    session_id: str
    audio_bytes: bytes
    sequence_number: int = 0
    is_final: bool = False


class ProcessAudioChunkHandler(CommandHandler[ProcessAudioChunkCommand, VoiceSessionDTO]):
    """Handler executing ProcessAudioChunkCommand via STTPort."""

    def __init__(
        self,
        session_repository: VoiceSessionRepository,
        stt_port: STTPort,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = session_repository
        self._stt = stt_port
        self._uow = unit_of_work
        self._can_accept_spec = CanAcceptAudioSpec()

    async def handle(self, command: ProcessAudioChunkCommand) -> Result[VoiceSessionDTO]:
        """Execute audio chunk STT processing."""
        if not command.session_id:
            return Result.fail(Error("VALIDATION_ERROR", "session_id required"))

        session = await self._repo.get_by_id(EntityId(command.session_id))
        if session is None:
            return Result.fail(Error("NOT_FOUND", f"VoiceSession '{command.session_id}' not found"))

        if not self._can_accept_spec.is_satisfied_by(session):
            return Result.fail(Error("INVALID_STATE", "VoiceSession cannot accept audio in current state"))

        chunk = AudioChunk(
            payload=command.audio_bytes,
            sequence_number=command.sequence_number,
            is_final=command.is_final,
        )

        inbound_stream = next((s for s in session.streams if s.stream_type == "INBOUND"), None)
        if inbound_stream:
            inbound_stream.record_chunk(len(command.audio_bytes))

        # Perform STT transcription via port
        fmt = inbound_stream.audio_format if inbound_stream else None
        if fmt is None:
            return Result.fail(Error("INVALID_STATE", "Inbound stream format missing"))

        transcript, confidence = await self._stt.transcribe_audio_chunk(chunk, fmt)

        if transcript.strip():
            # Start user turn if needed
            active_turn = next((t for t in session.turns if not t.is_completed and t.speaker_role == "USER"), None)
            if active_turn is None:
                turn_res = session.start_turn("USER")
                if turn_res.is_failure:
                    return Result.fail(turn_res.error)
                active_turn = turn_res.value

            session.record_speech_transcribed(str(active_turn.id.value), transcript, confidence)

        async with self._uow:
            await self._repo.save(session)
            await self._uow.commit()

        return Result.ok(VoiceMapper.to_dto(session))
