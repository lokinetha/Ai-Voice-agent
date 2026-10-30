"""
Integration tests for Playbook Infrastructure and Bootstrap.
"""

from __future__ import annotations

import unittest

from playbook.domain.factories.playbook_factory import PlaybookFactory
from playbook.domain.value_objects.communication_style import (
    CommunicationStyle,
    FormalityLevel,
    PacingType,
    ToneType,
)
from playbook.domain.value_objects.persona import Persona
from playbook.domain.value_objects.playbook_status import PlaybookStatusType
from shared.kernel.value_objects import WorkspaceId


class TestPlaybookInfrastructure(unittest.TestCase):
    """Integration tests for Playbook infrastructure default values and mappings."""

    def test_factory_defaults_and_value_objects(self) -> None:
        persona = Persona(
            name="Alex",
            role="Support Engineer",
            description="Technical support rep",
            industry="Cloud Computing",
        )
        comm_style = CommunicationStyle(
            tone=ToneType.EMPATHETIC,
            formality=FormalityLevel.INFORMAL,
            pacing=PacingType.FAST,
            vocabulary_level=4,
            use_filler_words=True,
        )

        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-infra"),
            name="Support Playbook",
            persona=persona,
            communication_style=comm_style,
        )

        self.assertEqual(pb.status.value, PlaybookStatusType.DRAFT)
        self.assertIsNotNone(pb.persona)
        self.assertEqual(pb.persona.name, "Alex")
        self.assertEqual(pb.communication_style.tone, ToneType.EMPATHETIC)
        self.assertEqual(pb.communication_style.formality, FormalityLevel.INFORMAL)
        self.assertEqual(pb.communication_style.pacing, PacingType.FAST)
        self.assertTrue(pb.communication_style.use_filler_words)

    def test_playbook_aggregate_identity(self) -> None:
        pb1 = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Playbook A",
        )
        pb2 = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Playbook B",
        )

        self.assertNotEqual(pb1, pb2)
        self.assertNotEqual(pb1.id, pb2.id)


if __name__ == "__main__":
    unittest.main()
