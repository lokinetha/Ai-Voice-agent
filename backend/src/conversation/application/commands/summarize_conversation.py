"""
SummarizeConversation Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass, field

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
from conversation.domain.value_objects.conversation_summary import (
    ConversationSummary,
)


@dataclass(frozen=True)
class SummarizeConversationCommand(Command):
    """Command requesting Conversation summarization."""

    conversation_id: str
    summary_text: str
    key_topics: tuple[str, ...] = field(default_factory=tuple)
    sentiment: str = "neutral"
    action_items: tuple[str, ...] = field(default_factory=tuple)


class SummarizeConversationHandler(CommandHandler[SummarizeConversationCommand, ConversationDTO]):
    """Handler executing SummarizeConversationCommand."""

    def __init__(
        self,
        conv_repository: ConversationRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._conv_repo = conv_repository
        self._uow = unit_of_work

    async def handle(self, command: SummarizeConversationCommand) -> Result[ConversationDTO]:
        """Execute conversation summarization."""
        conv = await self._conv_repo.get_by_id(ConversationId(command.conversation_id))
        if conv is None:
            return Result.fail(Error("NOT_FOUND", f"Conversation '{command.conversation_id}' not found"))

        try:
            summary = ConversationSummary(
                text=command.summary_text,
                key_topics=command.key_topics,
                sentiment=command.sentiment,
                action_items=command.action_items,
            )
        except ValueError as err:
            return Result.fail(Error("VALIDATION_ERROR", str(err)))

        sum_res = conv.summarize(summary)
        if sum_res.is_failure:
            return Result.fail(sum_res.error)

        async with self._uow:
            await self._conv_repo.save(conv)
            await self._uow.commit()

        return Result.ok(ConversationMapper.to_conversation_dto(conv))
