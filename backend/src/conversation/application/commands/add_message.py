"""
AddMessage Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import ConversationId, EntityId, MessageId

from conversation.application.dto.conversation_dto import ConversationDTO
from conversation.application.mappers.conversation_mapper import (
    ConversationMapper,
)
from conversation.domain.entities.message import Message
from conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from conversation.domain.value_objects.participant_role import (
    ParticipantRole,
    RoleCategory,
)


@dataclass(frozen=True)
class AddMessageCommand(Command):
    """Command requesting Message append to a Conversation."""

    conversation_id: str
    participant_id: str
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class AddMessageHandler(CommandHandler[AddMessageCommand, ConversationDTO]):
    """Handler executing AddMessageCommand."""

    def __init__(
        self,
        conv_repository: ConversationRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._conv_repo = conv_repository
        self._uow = unit_of_work

    async def handle(self, command: AddMessageCommand) -> Result[ConversationDTO]:
        """Execute message addition."""
        conv = await self._conv_repo.get_by_id(ConversationId(command.conversation_id))
        if conv is None:
            return Result.fail(Error("NOT_FOUND", f"Conversation '{command.conversation_id}' not found"))

        try:
            role = ParticipantRole(RoleCategory(command.role.upper()))
        except ValueError:
            return Result.fail(Error("VALIDATION_ERROR", f"Invalid participant role: {command.role}"))

        message = Message(
            id=MessageId(),
            participant_id=EntityId(command.participant_id),
            role=role,
            content=command.content,
            sequence_number=conv.message_count,
            metadata=command.metadata,
        )

        add_res = conv.add_message(message)
        if add_res.is_failure:
            return Result.fail(add_res.error)

        async with self._uow:
            await self._conv_repo.save(conv)
            await self._uow.commit()

        return Result.ok(ConversationMapper.to_conversation_dto(conv))
