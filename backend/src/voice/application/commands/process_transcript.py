"""
ProcessTranscript Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import EntityId

from voice.application.dto.voice_dto import VoiceSessionDTO
from voice.application.mappers.voice_mapper import VoiceMapper
from voice.domain.ports.conversation_port import ConversationPort
from voice.domain.repositories.voice_session_repository import (
    VoiceSessionRepository,
)


@dataclass(frozen=True)
class ProcessTranscriptCommand(Command):
    """Command recording transcribed user speech turn into target Conversation aggregate."""

    session_id: str
    transcript: str
    confidence: float = 1.0


class ProcessTranscriptHandler(CommandHandler[ProcessTranscriptCommand, VoiceSessionDTO]):
    """Handler executing ProcessTranscriptCommand via ConversationPort."""

    def __init__(
        self,
        session_repository: VoiceSessionRepository,
        conversation_port: ConversationPort,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = session_repository
        self._conv_port = conversation_port
        self._uow = unit_of_work

    async def handle(self, command: ProcessTranscriptCommand) -> Result[VoiceSessionDTO]:
        """Execute ProcessTranscriptCommand."""
        if not command.session_id or not command.transcript:
            return Result.fail(Error("VALIDATION_ERROR", "session_id and transcript required"))

        session = await self._repo.get_by_id(EntityId(command.session_id))
        if session is None:
            return Result.fail(Error("NOT_FOUND", f"VoiceSession '{command.session_id}' not found"))

        # Append message turn to Conversation via application port
        await self._conv_port.append_message_to_conversation(
            conversation_id=str(session.conversation_id.value),
            role="CUSTOMER",
            content=command.transcript,
        )

        active_turn = next((t for t in session.turns if not t.is_completed and t.speaker_role == "USER"), None)
        if active_turn is None:
            turn_res = session.start_turn("USER")
            if turn_res.is_failure:
                return Result.fail(turn_res.error)
            active_turn = turn_res.value

        session.record_speech_transcribed(
            str(active_turn.id.value), command.transcript, command.confidence
        )

        async with self._uow:
            await self._repo.save(session)
            await self._uow.commit()

        return Result.ok(VoiceMapper.to_dto(session))
