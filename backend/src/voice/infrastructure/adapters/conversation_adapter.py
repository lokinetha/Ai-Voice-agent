"""
ConversationAdapter implementing ConversationPort.

Adapts the Conversation bounded context command handlers to record voice-session
turns into the Conversation aggregate root.
"""

from __future__ import annotations

from typing import Any

from voice.domain.ports.conversation_port import ConversationPort


class ConversationAdapter(ConversationPort):
    """Adapter recording voice turns into target Conversation aggregates."""

    def __init__(self, session: Any = None) -> None:
        self._session = session

    async def append_message_to_conversation(
        self, conversation_id: str, role: str, content: str
    ) -> str:
        """Record turn in Conversation aggregate."""
        if self._session is None:
            return f"msg-{conversation_id}"

        from conversation.application.commands.add_message import (
            AddMessageCommand,
            AddMessageHandler,
        )
        from identity.bootstrap.dependency_injection import SqlAlchemyUnitOfWork

        conv_repo = SqlAlchemyConversationRepository_Placeholder(self._session)
        uow = SqlAlchemyUnitOfWork(self._session)

        handler = AddMessageHandler(
            conv_repository=conv_repo,  # type: ignore[arg-type]
            unit_of_work=uow,
        )
        res = await handler.handle(
            AddMessageCommand(
                conversation_id=conversation_id,
                participant_id=f"voice-{role.lower()}",
                content=content,
                role=role,
            )
        )
        if res.is_success:
            return res.value.id
        return f"msg-{conversation_id}"


class SqlAlchemyConversationRepository_Placeholder:
    """Helper delegating to SqlAlchemyConversationRepository."""

    def __init__(self, session: Any) -> None:
        from conversation.infrastructure.persistence.sqlalchemy_conversation_repository import (
            SqlAlchemyConversationRepository,
        )

        self._inner = SqlAlchemyConversationRepository(session)

    def __getattr__(self, name: str) -> object:
        return getattr(self._inner, name)
