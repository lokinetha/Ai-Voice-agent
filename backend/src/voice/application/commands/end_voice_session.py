"""
EndVoiceSession Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import EntityId

from voice.application.dto.voice_dto import VoiceSessionDTO
from voice.application.mappers.voice_mapper import VoiceMapper
from voice.domain.ports.telephony_port import TelephonyPort
from voice.domain.repositories.voice_session_repository import (
    VoiceSessionRepository,
)
from voice.domain.services.voice_session_lifecycle_service import (
    VoiceSessionLifecycleService,
)


@dataclass(frozen=True)
class EndVoiceSessionCommand(Command):
    """Command requesting end/termination of an active VoiceSession."""

    session_id: str
    reason: str = "User hangup"


class EndVoiceSessionHandler(CommandHandler[EndVoiceSessionCommand, VoiceSessionDTO]):
    """Handler executing EndVoiceSessionCommand."""

    def __init__(
        self,
        session_repository: VoiceSessionRepository,
        telephony_port: TelephonyPort,
        lifecycle_service: VoiceSessionLifecycleService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = session_repository
        self._telephony = telephony_port
        self._lifecycle_service = lifecycle_service
        self._uow = unit_of_work

    async def handle(self, command: EndVoiceSessionCommand) -> Result[VoiceSessionDTO]:
        """Execute EndVoiceSessionCommand."""
        if not command.session_id:
            return Result.fail(Error("VALIDATION_ERROR", "session_id required"))

        session = await self._repo.get_by_id(EntityId(command.session_id))
        if session is None:
            return Result.fail(Error("NOT_FOUND", f"VoiceSession '{command.session_id}' not found"))

        check_res = self._lifecycle_service.can_end_session(session)
        if check_res.is_failure:
            return Result.fail(check_res.error)

        await self._telephony.terminate_call(connection_id=command.session_id)
        session.end(reason=command.reason)

        async with self._uow:
            await self._repo.save(session)
            await self._uow.commit()

        return Result.ok(VoiceMapper.to_dto(session))
