"""
Integration tests for Agent Infrastructure persistence implementation.
"""

from __future__ import annotations

import unittest

from agent.domain.factories.agent_factory import AgentFactory
from agent.domain.value_objects.agent_status import AgentStatusType
from shared.kernel.value_objects import WorkspaceId


class TestAgentInfrastructure(unittest.TestCase):
    def test_agent_factory_defaults(self) -> None:
        ws_id = WorkspaceId("ws-infra-1")
        agent = AgentFactory.create(workspace_id=ws_id, name="Infra Test Agent")

        self.assertEqual(agent.name, "Infra Test Agent")
        self.assertEqual(agent.status.value, AgentStatusType.DRAFT)
        self.assertEqual(agent.voice_config.tts_provider, "elevenlabs")
        self.assertEqual(agent.llm_config.provider, "gemini")


if __name__ == "__main__":
    unittest.main()
