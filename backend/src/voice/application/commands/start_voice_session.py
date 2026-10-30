"""
StartVoiceSession Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import (
    AgentId,
    ConversationId,
    WorkspaceId,
)

from voice.application.dto.voice_dto import VoiceSessionDTO
from voice.application.mappers.voice_mapper import VoiceMapper
from voice.domain.factories.voice_session_factory import VoiceSessionFactory
from voice.domain.repositories.voice_session_repository import (
    VoiceSessionRepository,
)
from voice.domain.services.voice_session_lifecycle_service import (
    VoiceSessionLifecycleService,
)
from voice.domain.value_objects.audio_format import AudioFormat
from voice.domain.value_objects.voice_provider import VoiceProvider


@dataclass(frozen=True)
class StartVoiceSessionCommand(Command):
    """Command requesting start of a new VoiceSession."""

    workspace_id: str
    agent_id: str
    conversation_id: str
    stt_provider_name: str = "fake_stt"
    tts_provider_name: str = "fake_tts"
    telephony_provider_name: str = "fake_telephony"
    sample_rate: int = 16000
    channels: int = 1
    encoding: str = "pcm_s16le"


class StartVoiceSessionHandler(CommandHandler[StartVoiceSessionCommand, VoiceSessionDTO]):
    """Handler executing StartVoiceSessionCommand."""

    def __init__(
        self,
        session_repository: VoiceSessionRepository,
        lifecycle_service: VoiceSessionLifecycleService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = session_repository
        self._lifecycle_service = lifecycle_service
        self._uow = unit_of_work

    async def handle(self, command: StartVoiceSessionCommand) -> Result[VoiceSessionDTO]:
        """Execute StartVoiceSessionCommand."""
        if not command.workspace_id or not command.agent_id or not command.conversation_id:
            return Result.fail(Error("VALIDATION_ERROR", "workspace_id, agent_id, and conversation_id required"))

        fmt = AudioFormat(
            sample_rate=command.sample_rate,
            channels=command.channels,
            encoding=command.encoding,
        )

        session = VoiceSessionFactory.create(
            workspace_id=WorkspaceId(command.workspace_id),
            agent_id=AgentId(command.agent_id),
            conversation_id=ConversationId(command.conversation_id),
            stt_provider=VoiceProvider(command.stt_provider_name),
            tts_provider=VoiceProvider(command.tts_provider_name),
            telephony_provider=VoiceProvider(command.telephony_provider_name),
            audio_format=fmt,
        )

        check_res = self._lifecycle_service.can_start_session(session)
        if check_res.is_failure:
            return Result.fail(check_res.error)

        session.start()

        async with self._uow:
            await self._repo.save(session)
            await self._uow.commit()

        return Result.ok(VoiceMapper.to_dto(session))
