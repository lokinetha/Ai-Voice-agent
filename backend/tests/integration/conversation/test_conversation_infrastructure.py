"""
Integration tests for Conversation Infrastructure and Bootstrap.
"""

from __future__ import annotations

import unittest

from conversation.domain.factories.conversation_factory import (
    ConversationFactory,
)
from conversation.domain.value_objects.conversation_channel import (
    ConversationChannel,
)
from conversation.domain.value_objects.conversation_status import (
    ConversationStatusType,
)
from shared.kernel.value_objects import AgentId, WorkspaceId


class TestConversationInfrastructure(unittest.TestCase):
    """Integration tests for Conversation infrastructure defaults."""

    def test_factory_defaults_and_language(self) -> None:
        conv = ConversationFactory.create(
            workspace_id=WorkspaceId("ws-infra"),
            agent_id=AgentId("agent-infra"),
            channel=ConversationChannel.api(),
            participant_name="Test User",
        )

        self.assertEqual(conv.status.value, ConversationStatusType.ACTIVE)
        self.assertEqual(conv.language.code, "en-US")
        self.assertEqual(conv.channel.value.value, "API")
        self.assertEqual(conv.participant_count, 2)
        self.assertIsNotNone(conv.memory)
        self.assertIsNotNone(conv.timeline)

    def test_conversation_aggregate_identity(self) -> None:
        conv1 = ConversationFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            agent_id=AgentId("a-1"),
            channel=ConversationChannel.voice(),
            participant_name="User A",
        )
        conv2 = ConversationFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            agent_id=AgentId("a-1"),
            channel=ConversationChannel.voice(),
            participant_name="User B",
        )

        self.assertNotEqual(conv1, conv2)
        self.assertNotEqual(conv1.id, conv2.id)


if __name__ == "__main__":
    unittest.main()
