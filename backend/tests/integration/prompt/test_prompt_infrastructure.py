"""
Integration tests for Prompt Infrastructure and Bootstrap.
"""

from __future__ import annotations

import unittest

from prompt.domain.factories.prompt_factory import PromptFactory
from prompt.domain.value_objects.prompt_status import PromptStatusType
from prompt.domain.value_objects.prompt_template import PromptTemplate
from shared.kernel.value_objects import WorkspaceId


class TestPromptInfrastructure(unittest.TestCase):
    """Integration tests for Prompt infrastructure defaults and template mappings."""

    def test_factory_defaults_and_template(self) -> None:
        template = PromptTemplate(
            name="CUSTOM_TEMPLATE",
            prefix="=== START ===",
            suffix="=== END ===",
        )

        prompt = PromptFactory.create(
            workspace_id=WorkspaceId("ws-infra"),
            name="System Prompt Template",
            template=template,
        )

        self.assertEqual(prompt.status.value, PromptStatusType.DRAFT)
        self.assertEqual(prompt.template.name, "CUSTOM_TEMPLATE")
        self.assertEqual(prompt.template.prefix, "=== START ===")
        self.assertEqual(prompt.template.suffix, "=== END ===")

    def test_prompt_aggregate_identity(self) -> None:
        p1 = PromptFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Prompt A",
        )
        p2 = PromptFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Prompt B",
        )

        self.assertNotEqual(p1, p2)
        self.assertNotEqual(p1.id, p2.id)


if __name__ == "__main__":
    unittest.main()
