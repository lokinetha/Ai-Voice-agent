"""
Unit tests for Conversation Application Command and Query Handlers.
"""

from __future__ import annotations

import asyncio
import unittest
from typing import Self

from conversation.application.commands.add_message import (
    AddMessageCommand,
    AddMessageHandler,
)
from conversation.application.commands.end_conversation import (
    EndConversationCommand,
    EndConversationHandler,
)
from conversation.application.commands.pause_conversation import (
    PauseConversationCommand,
    PauseConversationHandler,
)
from conversation.application.commands.resume_conversation import (
    ResumeConversationCommand,
    ResumeConversationHandler,
)
from conversation.application.commands.start_conversation import (
    StartConversationCommand,
    StartConversationHandler,
)
from conversation.application.commands.summarize_conversation import (
    SummarizeConversationCommand,
    SummarizeConversationHandler,
)
from conversation.application.queries.get_conversation import (
    GetConversationHandler,
    GetConversationQuery,
)
from conversation.application.queries.get_conversation_messages import (
    GetConversationMessagesHandler,
    GetConversationMessagesQuery,
)
from conversation.application.queries.list_conversations import (
    ListConversationsHandler,
    ListConversationsQuery,
)
from conversation.domain.entities.conversation import Conversation
from conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from conversation.domain.services.conversation_lifecycle_service import (
    ConversationLifecycleService,
)
from shared.kernel.domain_event import DomainEvent
from shared.kernel.specification import Specification
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import AgentId, ConversationId, WorkspaceId


class InMemoryConversationRepository(ConversationRepository):
    """In-memory test double for ConversationRepository."""

    def __init__(self) -> None:
        self.store: dict[str, Conversation] = {}

    async def get_by_id(self, id: ConversationId) -> Conversation | None:
        return self.store.get(str(id.value))

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[Conversation]:
        return [c for c in self.store.values() if c.workspace_id == workspace_id]

    async def find_by_agent(self, agent_id: AgentId) -> list[Conversation]:
        return [c for c in self.store.values() if c.agent_id == agent_id]

    async def save(self, aggregate: Conversation) -> None:
        self.store[str(aggregate.id.value)] = aggregate

    async def delete(self, aggregate: Conversation) -> None:
        self.store.pop(str(aggregate.id.value), None)

    async def find(self, spec: Specification[Conversation]) -> list[Conversation]:
        return [c for c in self.store.values() if spec.is_satisfied_by(c)]

    async def count(self, spec: Specification[Conversation]) -> int:
        return len(await self.find(spec))


class DummyUnitOfWork(UnitOfWork):
    """Test double for UnitOfWork."""

    def __init__(self) -> None:
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass

    def collect_events(self) -> list[DomainEvent]:
        return []


class TestConversationHandlers(unittest.TestCase):
    """Tests for Conversation CQRS Handlers."""

    def setUp(self) -> None:
        self.repo = InMemoryConversationRepository()
        self.uow = DummyUnitOfWork()
        self.lifecycle_svc = ConversationLifecycleService()

    def test_start_conversation_success(self) -> None:
        async def run() -> None:
            handler = StartConversationHandler(self.repo, self.uow)
            cmd = StartConversationCommand(
                workspace_id="ws-1",
                agent_id="agent-1",
                channel="VOICE",
                participant_name="John Doe",
            )
            result = await handler.handle(cmd)
            self.assertTrue(result.is_success)
            self.assertEqual(result.value.status, "ACTIVE")
            self.assertEqual(result.value.participant_count, 2)

        asyncio.run(run())

    def test_add_message_and_get_messages(self) -> None:
        async def run() -> None:
            start_h = StartConversationHandler(self.repo, self.uow)
            start_res = await start_h.handle(
                StartConversationCommand(
                    workspace_id="ws-1",
                    agent_id="agent-1",
                    channel="WEBCHAT",
                    participant_name="Alice",
                )
            )
            conv_id = start_res.value.id
            customer_id = [
                p.id for p in start_res.value.participants if p.role == "CUSTOMER"
            ][0]

            msg_h = AddMessageHandler(self.repo, self.uow)
            msg_res = await msg_h.handle(
                AddMessageCommand(
                    conversation_id=conv_id,
                    participant_id=customer_id,
                    role="CUSTOMER",
                    content="Hello, I need help with billing.",
                )
            )
            self.assertTrue(msg_res.is_success)
            self.assertEqual(msg_res.value.message_count, 1)

            msgs_h = GetConversationMessagesHandler(self.repo)
            msgs_res = await msgs_h.handle(
                GetConversationMessagesQuery(conversation_id=conv_id)
            )
            self.assertTrue(msgs_res.is_success)
            self.assertEqual(len(msgs_res.value), 1)

        asyncio.run(run())

    def test_pause_resume_end_lifecycle(self) -> None:
        async def run() -> None:
            start_h = StartConversationHandler(self.repo, self.uow)
            start_res = await start_h.handle(
                StartConversationCommand(
                    workspace_id="ws-1",
                    agent_id="agent-1",
                    channel="VOICE",
                    participant_name="Bob",
                )
            )
            conv_id = start_res.value.id

            # Pause
            pause_h = PauseConversationHandler(self.repo, self.uow)
            pause_res = await pause_h.handle(
                PauseConversationCommand(conversation_id=conv_id, reason="hold")
            )
            self.assertTrue(pause_res.is_success)
            self.assertEqual(pause_res.value.status, "PAUSED")

            # Resume
            resume_h = ResumeConversationHandler(self.repo, self.uow)
            resume_res = await resume_h.handle(
                ResumeConversationCommand(conversation_id=conv_id)
            )
            self.assertTrue(resume_res.is_success)
            self.assertEqual(resume_res.value.status, "ACTIVE")

            # End
            end_h = EndConversationHandler(self.repo, self.lifecycle_svc, self.uow)
            end_res = await end_h.handle(
                EndConversationCommand(conversation_id=conv_id, reason="completed")
            )
            self.assertTrue(end_res.is_success)
            self.assertEqual(end_res.value.status, "ENDED")

        asyncio.run(run())

    def test_summarize_after_end(self) -> None:
        async def run() -> None:
            start_h = StartConversationHandler(self.repo, self.uow)
            start_res = await start_h.handle(
                StartConversationCommand(
                    workspace_id="ws-1",
                    agent_id="agent-1",
                    channel="VOICE",
                    participant_name="Carol",
                )
            )
            conv_id = start_res.value.id

            end_h = EndConversationHandler(self.repo, self.lifecycle_svc, self.uow)
            await end_h.handle(EndConversationCommand(conversation_id=conv_id, reason="done"))

            sum_h = SummarizeConversationHandler(self.repo, self.uow)
            sum_res = await sum_h.handle(
                SummarizeConversationCommand(
                    conversation_id=conv_id,
                    summary_text="Customer inquired about billing.",
                    key_topics=("billing", "refund"),
                    sentiment="neutral",
                )
            )
            self.assertTrue(sum_res.is_success)

        asyncio.run(run())

    def test_get_conversation_query(self) -> None:
        async def run() -> None:
            start_h = StartConversationHandler(self.repo, self.uow)
            start_res = await start_h.handle(
                StartConversationCommand(
                    workspace_id="ws-1",
                    agent_id="agent-1",
                    channel="VOICE",
                    participant_name="Dave",
                )
            )
            conv_id = start_res.value.id

            get_h = GetConversationHandler(self.repo)
            get_res = await get_h.handle(GetConversationQuery(conversation_id=conv_id))
            self.assertTrue(get_res.is_success)
            self.assertEqual(get_res.value.id, conv_id)

        asyncio.run(run())

    def test_list_conversations_query(self) -> None:
        async def run() -> None:
            start_h = StartConversationHandler(self.repo, self.uow)
            await start_h.handle(
                StartConversationCommand(
                    workspace_id="ws-list",
                    agent_id="agent-1",
                    channel="WEBCHAT",
                    participant_name="Eve",
                )
            )
            await start_h.handle(
                StartConversationCommand(
                    workspace_id="ws-list",
                    agent_id="agent-2",
                    channel="VOICE",
                    participant_name="Frank",
                )
            )

            list_h = ListConversationsHandler(self.repo)
            list_res = await list_h.handle(ListConversationsQuery(workspace_id="ws-list"))
            self.assertTrue(list_res.is_success)
            self.assertEqual(len(list_res.value), 2)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
