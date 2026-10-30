"""
Unit tests for Agent Application Command and Query Handlers.
"""

from __future__ import annotations

import asyncio
import unittest

from agent.application.commands.clone_agent import (
    CloneAgentCommand,
    CloneAgentHandler,
)
from agent.application.commands.create_agent import (
    CreateAgentCommand,
    CreateAgentHandler,
)
from agent.application.commands.publish_agent import (
    PublishAgentCommand,
    PublishAgentHandler,
)
from agent.application.commands.update_agent import (
    UpdateAgentCommand,
    UpdateAgentHandler,
)
from agent.application.queries.get_agent import GetAgentHandler, GetAgentQuery
from agent.application.queries.list_agents import (
    ListAgentsHandler,
    ListAgentsQuery,
)
from agent.domain.entities.agent import Agent
from agent.domain.repositories.agent_repository import AgentRepository
from agent.domain.services.agent_publishing_service import AgentPublishingService
from shared.kernel.domain_event import DomainEvent
from shared.kernel.specification import Specification
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import AgentId, WorkspaceId


class InMemoryAgentRepository(AgentRepository):
    def __init__(self) -> None:
        self.agents: dict[str, Agent] = {}

    async def get_by_id(self, id: AgentId) -> Agent | None:
        return self.agents.get(str(id.value))

    async def get_by_workspace_and_name(
        self, workspace_id: WorkspaceId, name: str
    ) -> Agent | None:
        for a in self.agents.values():
            if a.workspace_id == workspace_id and a.name.lower() == name.strip().lower():
                return a
        return None

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[Agent]:
        return [a for a in self.agents.values() if a.workspace_id == workspace_id]

    async def save(self, aggregate: Agent) -> None:
        self.agents[str(aggregate.id.value)] = aggregate

    async def delete(self, aggregate: Agent) -> None:
        self.agents.pop(str(aggregate.id.value), None)

    async def find(self, spec: Specification[Agent]) -> list[Agent]:
        return [a for a in self.agents.values() if spec.is_satisfied_by(a)]

    async def count(self, spec: Specification[Agent]) -> int:
        return len(await self.find(spec))


class DummyUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.committed = False

    async def __aenter__(self) -> DummyUnitOfWork:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass

    def collect_events(self) -> list[DomainEvent]:
        return []


class TestAgentApplicationHandlers(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryAgentRepository()
        self.uow = DummyUnitOfWork()
        self.pub_svc = AgentPublishingService()

    def test_create_agent_unique_name_invariant(self) -> None:
        async def run() -> None:
            handler = CreateAgentHandler(self.repo, self.uow)

            res1 = await handler.handle(
                CreateAgentCommand(workspace_id="ws-100", name="Outbound Sales", agent_type="SALES")
            )
            self.assertTrue(res1.is_success)

            # Duplicate name attempt in same workspace -> CONFLICT
            res2 = await handler.handle(
                CreateAgentCommand(workspace_id="ws-100", name="Outbound Sales", agent_type="SALES")
            )
            self.assertTrue(res2.is_failure)
            self.assertEqual(res2.error.code, "CONFLICT")

        asyncio.run(run())

    def test_publish_agent_precondition_invariant(self) -> None:
        async def run() -> None:
            create_h = CreateAgentHandler(self.repo, self.uow)
            create_res = await create_h.handle(
                CreateAgentCommand(workspace_id="ws-100", name="Telesales Bot")
            )
            agent_id = create_res.value.id

            pub_h = PublishAgentHandler(self.repo, self.pub_svc, self.uow)

            # Publish without Playbook/Prompt -> PRECONDITION_FAILED
            pub_res1 = await pub_h.handle(PublishAgentCommand(agent_id=agent_id))
            self.assertTrue(pub_res1.is_failure)
            self.assertEqual(pub_res1.error.code, "PRECONDITION_FAILED")

            # Associate playbook and prompt via update
            update_h = UpdateAgentHandler(self.repo, self.uow)
            await update_h.handle(
                UpdateAgentCommand(agent_id=agent_id, playbook_id="pb-1", prompt_id="pmt-1")
            )

            # Publish again -> Success
            pub_res2 = await pub_h.handle(PublishAgentCommand(agent_id=agent_id))
            self.assertTrue(pub_res2.is_success)
            self.assertEqual(pub_res2.value.status, "PUBLISHED")

        asyncio.run(run())

    def test_clone_agent_handler(self) -> None:
        async def run() -> None:
            create_h = CreateAgentHandler(self.repo, self.uow)
            create_res = await create_h.handle(
                CreateAgentCommand(workspace_id="ws-100", name="Original Bot")
            )
            agent_id = create_res.value.id

            clone_h = CloneAgentHandler(self.repo, self.uow)
            clone_res = await clone_h.handle(
                CloneAgentCommand(source_agent_id=agent_id, new_name="Cloned Bot")
            )
            self.assertTrue(clone_res.is_success)
            self.assertEqual(clone_res.value.name, "Cloned Bot")
            self.assertNotEqual(clone_res.value.id, agent_id)

        asyncio.run(run())

    def test_get_and_list_agents_queries(self) -> None:
        async def run() -> None:
            create_h = CreateAgentHandler(self.repo, self.uow)
            await create_h.handle(CreateAgentCommand(workspace_id="ws-200", name="Agent Alpha"))
            await create_h.handle(CreateAgentCommand(workspace_id="ws-200", name="Agent Beta"))

            list_h = ListAgentsHandler(self.repo)
            list_res = await list_h.handle(ListAgentsQuery(workspace_id="ws-200"))
            self.assertTrue(list_res.is_success)
            self.assertEqual(len(list_res.value), 2)

            get_h = GetAgentHandler(self.repo)
            get_res = await get_h.handle(GetAgentQuery(agent_id=list_res.value[0].id))
            self.assertTrue(get_res.is_success)
            self.assertEqual(get_res.value.workspace_id, "ws-200")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
