"""
Integration tests for Knowledge Infrastructure persistence implementation.
"""

from __future__ import annotations

import unittest

from knowledge.domain.factories.knowledge_base_factory import KnowledgeBaseFactory
from knowledge.domain.value_objects.kb_status import KBStatusType
from shared.kernel.value_objects import WorkspaceId


class TestKnowledgeInfrastructure(unittest.TestCase):
    def test_knowledge_base_factory_defaults(self) -> None:
        ws_id = WorkspaceId("ws-infra-kb")
        kb = KnowledgeBaseFactory.create(workspace_id=ws_id, name="Infra Test KB")

        self.assertEqual(kb.name, "Infra Test KB")
        self.assertEqual(kb.status.value, KBStatusType.ACTIVE)
        self.assertEqual(kb.retrieval_policy.top_k, 5)
        self.assertEqual(kb.retrieval_policy.strategy, "hybrid")


if __name__ == "__main__":
    unittest.main()
