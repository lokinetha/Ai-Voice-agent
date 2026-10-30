"""
Unit tests for Playbook Domain Layer — Aggregate Root, Entities, Value Objects,
Factory, Specifications, and Domain Service.
"""

from __future__ import annotations

import unittest

from playbook.domain.entities.playbook_example import PlaybookExample
from playbook.domain.entities.playbook_goal import PlaybookGoal
from playbook.domain.entities.playbook_objection import PlaybookObjection
from playbook.domain.entities.playbook_rule import PlaybookRule
from playbook.domain.entities.playbook_stage import PlaybookStage
from playbook.domain.entities.playbook_transition import PlaybookTransition
from playbook.domain.events.playbook_archived import PlaybookArchived
from playbook.domain.events.playbook_created import PlaybookCreated
from playbook.domain.events.playbook_published import PlaybookPublished
from playbook.domain.events.playbook_version_created import PlaybookVersionCreated
from playbook.domain.factories.playbook_factory import PlaybookFactory
from playbook.domain.services.playbook_validation_service import (
    PlaybookValidationService,
)
from playbook.domain.specifications.publishable_playbook_spec import (
    PublishablePlaybookSpec,
)
from playbook.domain.specifications.valid_playbook_spec import ValidPlaybookSpec
from playbook.domain.value_objects.persona import Persona
from playbook.domain.value_objects.playbook_status import PlaybookStatusType
from shared.kernel.value_objects import EntityId, WorkspaceId


class TestPlaybookFactory(unittest.TestCase):
    """Tests for PlaybookFactory."""

    def test_factory_creates_playbook(self) -> None:
        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="SaaS Sales Playbook",
            description="B2B sales playbook",
        )

        self.assertEqual(pb.name, "SaaS Sales Playbook")
        self.assertEqual(pb.status.value, PlaybookStatusType.DRAFT)
        self.assertEqual(len(pb.domain_events), 1)
        self.assertIsInstance(pb.domain_events[0], PlaybookCreated)


class TestPlaybookAggregate(unittest.TestCase):
    """Tests for Playbook Aggregate Root rules and invariants."""

    def _make_valid_persona(self) -> Persona:
        return Persona(
            name="Sarah",
            role="Sales Rep",
            description="Friendly SaaS representative",
            industry="Technology",
        )

    def _make_goal(self) -> PlaybookGoal:
        return PlaybookGoal(
            id=EntityId(),
            name="Qualify Lead",
            description="Check budget and authority",
        )

    def test_cannot_publish_without_persona(self) -> None:
        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Incomplete Playbook",
        )
        pb.add_goal(self._make_goal())

        result = pb.publish()
        self.assertTrue(result.is_failure)
        self.assertEqual(result.error.code, "INVARIANT_VIOLATION")

    def test_cannot_publish_without_goals(self) -> None:
        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="No Goals Playbook",
            persona=self._make_valid_persona(),
        )

        result = pb.publish()
        self.assertTrue(result.is_failure)
        self.assertEqual(result.error.code, "INVARIANT_VIOLATION")

    def test_successful_publish(self) -> None:
        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Complete Playbook",
            persona=self._make_valid_persona(),
            initial_goals=[self._make_goal()],
        )
        pb.clear_events()

        result = pb.publish(label="v1.0", changelog="Initial release")
        self.assertTrue(result.is_success)
        self.assertEqual(pb.status.value, PlaybookStatusType.PUBLISHED)
        self.assertEqual(pb.version_info.version_number, 2)
        self.assertEqual(pb.version_info.label, "v1.0")

        events = pb.domain_events
        self.assertTrue(any(isinstance(e, PlaybookPublished) for e in events))
        self.assertTrue(any(isinstance(e, PlaybookVersionCreated) for e in events))

    def test_archive_playbook(self) -> None:
        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Playbook to Archive",
        )
        pb.clear_events()

        arch_res = pb.archive("Deprecated")
        self.assertTrue(arch_res.is_success)
        self.assertEqual(pb.status.value, PlaybookStatusType.ARCHIVED)
        self.assertTrue(any(isinstance(e, PlaybookArchived) for e in pb.domain_events))

    def test_cannot_modify_archived_playbook(self) -> None:
        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Archived Playbook",
        )
        pb.archive("Obsolete")

        self.assertTrue(pb.update_metadata("New Name").is_failure)
        self.assertTrue(pb.add_goal(self._make_goal()).is_failure)
        self.assertTrue(pb.publish().is_failure)

    def test_invalid_transition_between_missing_stages(self) -> None:
        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Bad Transition Playbook",
            persona=self._make_valid_persona(),
            initial_goals=[self._make_goal()],
        )
        t = PlaybookTransition(
            id=EntityId(),
            from_stage_id=EntityId("stage-x"),
            to_stage_id=EntityId("stage-y"),
        )

        res = pb.add_transition(t)
        self.assertTrue(res.is_failure)
        self.assertEqual(res.error.code, "INVARIANT_VIOLATION")

    def test_valid_stage_transition(self) -> None:
        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Multi Stage Playbook",
            persona=self._make_valid_persona(),
            initial_goals=[self._make_goal()],
        )
        s1 = PlaybookStage(id=EntityId(), name="Intro", order=1)
        s2 = PlaybookStage(id=EntityId(), name="Pitch", order=2)
        pb.add_stage(s1)
        pb.add_stage(s2)

        t = PlaybookTransition(
            id=EntityId(),
            from_stage_id=s1.id,
            to_stage_id=s2.id,
            condition="Intro completed",
        )
        res = pb.add_transition(t)
        self.assertTrue(res.is_success)
        self.assertEqual(len(pb.transitions), 1)

    def test_add_entities(self) -> None:
        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Rich Playbook",
        )
        rule = PlaybookRule(
            id=EntityId(),
            name="No swearing",
            condition="always",
            action="Maintain formal tone",
        )
        objection = PlaybookObjection(
            id=EntityId(),
            trigger_phrase="Too expensive",
            objection_category="PRICE",
            response_strategy="Highlight ROI",
        )
        example = PlaybookExample(
            id=EntityId(),
            scenario="Price inquiry",
            user_input="How much does it cost?",
            ideal_response="Our plans start at $49/mo.",
        )

        self.assertTrue(pb.add_rule(rule).is_success)
        self.assertTrue(pb.add_objection(objection).is_success)
        self.assertTrue(pb.add_example(example).is_success)

        self.assertEqual(len(pb.rules), 1)
        self.assertEqual(len(pb.objections), 1)
        self.assertEqual(len(pb.examples), 1)


class TestSpecifications(unittest.TestCase):
    """Tests for Playbook specifications."""

    def test_publishable_spec(self) -> None:
        spec = PublishablePlaybookSpec()
        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Test",
        )
        self.assertFalse(spec.is_satisfied_by(pb))

        pb.set_persona(
            Persona(name="P", role="R", description="D", industry="I")
        )
        pb.add_goal(PlaybookGoal(id=EntityId(), name="G"))
        self.assertTrue(spec.is_satisfied_by(pb))

    def test_valid_spec(self) -> None:
        spec = ValidPlaybookSpec()
        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Valid Playbook",
        )
        self.assertTrue(spec.is_satisfied_by(pb))


class TestPlaybookValidationService(unittest.TestCase):
    """Tests for PlaybookValidationService."""

    def test_service_can_publish(self) -> None:
        svc = PlaybookValidationService()
        pb = PlaybookFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Test",
        )
        self.assertFalse(svc.can_publish(pb))

        pb.set_persona(
            Persona(name="P", role="R", description="D", industry="I")
        )
        pb.add_goal(PlaybookGoal(id=EntityId(), name="G"))
        self.assertTrue(svc.can_publish(pb))


if __name__ == "__main__":
    unittest.main()
