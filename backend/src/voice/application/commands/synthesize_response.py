"""
SynthesizeResponse Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import EntityId

from voice.application.dto.voice_dto import VoiceSessionDTO
from voice.application.mappers.voice_mapper import VoiceMapper
from voice.domain.ports.audio_stream_port import AudioStreamPort
from voice.domain.ports.tts_port import TTSPort
from voice.domain.repositories.voice_session_repository import (
    VoiceSessionRepository,
)
from voice.domain.value_objects.audio_chunk import AudioChunk


@dataclass(frozen=True)
class SynthesizeResponseCommand(Command):
    """Command requesting TTS synthesis of agent response text into outbound audio stream."""

    session_id: str
    voice_id: str = "default_agent_voice"


class SynthesizeResponseHandler(CommandHandler[SynthesizeResponseCommand, VoiceSessionDTO]):
    """Handler executing SynthesizeResponseCommand via TTSPort and AudioStreamPort."""

    def __init__(self, session_repository: VoiceSessionRepository, tts_port: TTSPort, audio_stream_port: AudioStreamPort, unit_of_work: UnitOfWork) -> None:
        self._repo = session_repository
        self._tts = tts_port
        self._stream_port = audio_stream_port
        self._uow = unit_of_work

    async def handle(self, command: SynthesizeResponseCommand) -> Result[VoiceSessionDTO]:
        """Execute SynthesizeResponseCommand."""
        if not command.session_id:
            return Result.fail(Error("VALIDATION_ERROR", "session_id required"))

        session = await self._repo.get_by_id(EntityId(command.session_id))
        if session is None:
            return Result.fail(Error("NOT_FOUND", f"VoiceSession '{command.session_id}' not found"))

        # Find latest turn with agent response text
        target_turn = None
        for t in reversed(session.turns):
            if t.speaker_role == "AGENT" and t.agent_response_text and not t.audio_synthesized:
                target_turn = t
                break

        if target_turn is None:
            return Result.fail(Error("INVALID_STATE", "No pending unsynthesized agent turn found"))

        outbound_stream = next((s for s in session.streams if s.stream_type == "OUTBOUND"), None)
        fmt = outbound_stream.audio_format if outbound_stream else None
        if fmt is None:
            return Result.fail(Error("INVALID_STATE", "Outbound stream format missing"))

        # Synthesize TTS audio via port
        audio_bytes = await self._tts.synthesize_speech(
            text=target_turn.agent_response_text,
            voice_id=command.voice_id,
            audio_format=fmt,
        )

        if outbound_stream:
            outbound_stream.record_chunk(len(audio_bytes))
            await self._stream_port.send_audio_chunk(
                stream_id=str(outbound_stream.id.value),
                chunk=AudioChunk(payload=audio_bytes, is_final=True),
            )

        session.record_speech_synthesized(str(target_turn.id.value), len(audio_bytes))

        async with self._uow:
            await self._repo.save(session)
            await self._uow.commit()

        return Result.ok(VoiceMapper.to_dto(session))
