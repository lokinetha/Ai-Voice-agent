"""
Unit tests for Agent Domain Layer and Aggregate Invariants.
"""

from __future__ import annotations

import unittest

from agent.domain.events.agent_cloned import AgentCloned
from agent.domain.events.agent_created import AgentCreated
from agent.domain.events.agent_published import AgentPublished
from agent.domain.factories.agent_factory import AgentFactory
from agent.domain.services.agent_publishing_service import AgentPublishingService
from agent.domain.value_objects.agent_status import AgentStatusType
from agent.domain.value_objects.agent_type import AgentType
from shared.kernel.value_objects import PlaybookId, PromptId, WorkspaceId


class TestAgentDomain(unittest.TestCase):
    def test_agent_factory_creation(self) -> None:
        ws_id = WorkspaceId("ws-agent-1")
        agent = AgentFactory.create(
            workspace_id=ws_id,
            name="Inbound Support Agent",
            agent_type=AgentType.support(),
        )

        self.assertEqual(agent.name, "Inbound Support Agent")
        self.assertEqual(agent.workspace_id, ws_id)
        self.assertEqual(agent.status.value, AgentStatusType.DRAFT)
        self.assertIsNone(agent.playbook_id)
        self.assertIsNone(agent.prompt_id)

        events = agent.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], AgentCreated)

    def test_cannot_publish_without_playbook(self) -> None:
        agent = AgentFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Test Agent",
        )
        # Attempt to publish without playbook or prompt
        res = agent.publish()
        self.assertTrue(res.is_failure)
        self.assertEqual(res.error.code, "PRECONDITION_FAILED")
        self.assertIn("Playbook", res.error.message)

    def test_cannot_publish_without_prompt(self) -> None:
        agent = AgentFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Test Agent",
        )
        agent.set_playbook_id(PlaybookId("pb-100"))

        # Has playbook_id but missing prompt_id
        res = agent.publish()
        self.assertTrue(res.is_failure)
        self.assertEqual(res.error.code, "PRECONDITION_FAILED")
        self.assertIn("Prompt", res.error.message)

    def test_publish_success_when_invariants_satisfied(self) -> None:
        agent = AgentFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Publishable Agent",
        )
        agent.set_playbook_id(PlaybookId("pb-100"))
        agent.set_prompt_id(PromptId("pmt-200"))
        agent.clear_events()

        # Both Playbook and Prompt present -> publish succeeds
        res = agent.publish()
        self.assertTrue(res.is_success)
        self.assertEqual(agent.status.value, AgentStatusType.PUBLISHED)

        events = agent.domain_events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], AgentPublished)

    def test_agent_cloning(self) -> None:
        agent = AgentFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Original Agent",
        )
        agent.set_playbook_id(PlaybookId("pb-1"))
        agent.set_prompt_id(PromptId("pmt-1"))

        clone_res = agent.clone(new_name="Cloned Agent Copy")
        self.assertTrue(clone_res.is_success)

        cloned = clone_res.value
        self.assertEqual(cloned.name, "Cloned Agent Copy")
        self.assertNotEqual(cloned.id, agent.id)
        self.assertEqual(cloned.status.value, AgentStatusType.DRAFT)
        self.assertEqual(cloned.playbook_id, agent.playbook_id)

        events = cloned.domain_events
        self.assertTrue(any(isinstance(e, AgentCloned) for e in events))

    def test_publishing_service_validation(self) -> None:
        svc = AgentPublishingService()
        agent = AgentFactory.create(workspace_id=WorkspaceId("w"), name="Svc Test")

        self.assertTrue(svc.validate_and_publish(agent).is_failure)

        agent.set_playbook_id(PlaybookId("p1"))
        agent.set_prompt_id(PromptId("pr1"))
        self.assertTrue(svc.validate_and_publish(agent).is_success)


if __name__ == "__main__":
    unittest.main()
