"""
StartConversation Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import AgentId, WorkspaceId

from conversation.application.dto.conversation_dto import ConversationDTO
from conversation.application.mappers.conversation_mapper import (
    ConversationMapper,
)
from conversation.domain.factories.conversation_factory import (
    ConversationFactory,
)
from conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from conversation.domain.value_objects.conversation_channel import (
    ChannelType,
    ConversationChannel,
)
from conversation.domain.value_objects.conversation_language import (
    ConversationLanguage,
)


@dataclass(frozen=True)
class StartConversationCommand(Command):
    """Command requesting Conversation creation."""

    workspace_id: str
    agent_id: str
    channel: str
    participant_name: str
    customer_external_id: str = ""
    language: str = "en-US"


class StartConversationHandler(CommandHandler[StartConversationCommand, ConversationDTO]):
    """Handler executing StartConversationCommand."""

    def __init__(
        self,
        conv_repository: ConversationRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._conv_repo = conv_repository
        self._uow = unit_of_work

    async def handle(self, command: StartConversationCommand) -> Result[ConversationDTO]:
        """Execute Conversation creation."""
        if not command.participant_name or not command.participant_name.strip():
            return Result.fail(Error("VALIDATION_ERROR", "Participant name cannot be empty"))

        try:
            channel = ConversationChannel(ChannelType(command.channel.upper()))
        except ValueError:
            return Result.fail(Error("VALIDATION_ERROR", f"Invalid channel: {command.channel}"))

        try:
            language = ConversationLanguage(code=command.language)
        except ValueError:
            return Result.fail(Error("VALIDATION_ERROR", f"Invalid language code: {command.language}"))

        conv = ConversationFactory.create(
            workspace_id=WorkspaceId(command.workspace_id),
            agent_id=AgentId(command.agent_id),
            channel=channel,
            participant_name=command.participant_name,
            customer_external_id=command.customer_external_id,
            language=language,
        )

        async with self._uow:
            await self._conv_repo.save(conv)
            await self._uow.commit()

        return Result.ok(ConversationMapper.to_conversation_dto(conv, include_participants=True))
