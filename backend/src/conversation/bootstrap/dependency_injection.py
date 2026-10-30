"""
Conversation Bounded Context Dependency Injection Bootstrap.
"""

from __future__ import annotations

from identity.bootstrap.dependency_injection import SqlAlchemyUnitOfWork
from shared.kernel.unit_of_work import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

from conversation.application.commands.add_message import AddMessageHandler
from conversation.application.commands.end_conversation import (
    EndConversationHandler,
)
from conversation.application.commands.pause_conversation import (
    PauseConversationHandler,
)
from conversation.application.commands.resume_conversation import (
    ResumeConversationHandler,
)
from conversation.application.commands.start_conversation import (
    StartConversationHandler,
)
from conversation.application.commands.summarize_conversation import (
    SummarizeConversationHandler,
)
from conversation.application.queries.get_conversation import (
    GetConversationHandler,
)
from conversation.application.queries.get_conversation_messages import (
    GetConversationMessagesHandler,
)
from conversation.application.queries.list_conversations import (
    ListConversationsHandler,
)
from conversation.application.queries.search_conversation import (
    SearchConversationHandler,
)
from conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from conversation.domain.services.conversation_lifecycle_service import (
    ConversationLifecycleService,
)
from conversation.infrastructure.persistence.sqlalchemy_conversation_repository import (
    SqlAlchemyConversationRepository,
)


class ConversationContainer:
    """Dependency Container for Conversation Context services and handlers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._conv_repository: ConversationRepository = (
            SqlAlchemyConversationRepository(session)
        )
        self._lifecycle_service = ConversationLifecycleService()
        self._uow: UnitOfWork = SqlAlchemyUnitOfWork(session)

    @property
    def conv_repository(self) -> ConversationRepository:
        return self._conv_repository

    @property
    def lifecycle_service(self) -> ConversationLifecycleService:
        return self._lifecycle_service

    @property
    def unit_of_work(self) -> UnitOfWork:
        return self._uow

    def get_start_conversation_handler(self) -> StartConversationHandler:
        return StartConversationHandler(
            conv_repository=self._conv_repository,
            unit_of_work=self._uow,
        )

    def get_add_message_handler(self) -> AddMessageHandler:
        return AddMessageHandler(
            conv_repository=self._conv_repository,
            unit_of_work=self._uow,
        )

    def get_pause_conversation_handler(self) -> PauseConversationHandler:
        return PauseConversationHandler(
            conv_repository=self._conv_repository,
            unit_of_work=self._uow,
        )

    def get_resume_conversation_handler(self) -> ResumeConversationHandler:
        return ResumeConversationHandler(
            conv_repository=self._conv_repository,
            unit_of_work=self._uow,
        )

    def get_end_conversation_handler(self) -> EndConversationHandler:
        return EndConversationHandler(
            conv_repository=self._conv_repository,
            lifecycle_service=self._lifecycle_service,
            unit_of_work=self._uow,
        )

    def get_summarize_conversation_handler(self) -> SummarizeConversationHandler:
        return SummarizeConversationHandler(
            conv_repository=self._conv_repository,
            unit_of_work=self._uow,
        )

    def get_conversation_handler(self) -> GetConversationHandler:
        return GetConversationHandler(conv_repository=self._conv_repository)

    def get_list_conversations_handler(self) -> ListConversationsHandler:
        return ListConversationsHandler(conv_repository=self._conv_repository)

    def get_conversation_messages_handler(self) -> GetConversationMessagesHandler:
        return GetConversationMessagesHandler(conv_repository=self._conv_repository)

    def get_search_conversation_handler(self) -> SearchConversationHandler:
        return SearchConversationHandler(conv_repository=self._conv_repository)
