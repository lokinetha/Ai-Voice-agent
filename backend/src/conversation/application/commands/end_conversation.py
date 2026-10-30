"""
EndConversation Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import ConversationId

from conversation.application.dto.conversation_dto import ConversationDTO
from conversation.application.mappers.conversation_mapper import (
    ConversationMapper,
)
from conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from conversation.domain.services.conversation_lifecycle_service import (
    ConversationLifecycleService,
)


@dataclass(frozen=True)
class EndConversationCommand(Command):
    """Command requesting Conversation end."""

    conversation_id: str
    reason: str = ""


class EndConversationHandler(CommandHandler[EndConversationCommand, ConversationDTO]):
    """Handler executing EndConversationCommand."""

    def __init__(
        self,
        conv_repository: ConversationRepository,
        lifecycle_service: ConversationLifecycleService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._conv_repo = conv_repository
        self._lifecycle_service = lifecycle_service
        self._uow = unit_of_work

    async def handle(self, command: EndConversationCommand) -> Result[ConversationDTO]:
        """Execute conversation end."""
        conv = await self._conv_repo.get_by_id(ConversationId(command.conversation_id))
        if conv is None:
            return Result.fail(Error("NOT_FOUND", f"Conversation '{command.conversation_id}' not found"))

        end_res = self._lifecycle_service.end_conversation(conv, command.reason)
        if end_res.is_failure:
            return Result.fail(end_res.error)

        async with self._uow:
            await self._conv_repo.save(conv)
            await self._uow.commit()

        return Result.ok(ConversationMapper.to_conversation_dto(conv))
