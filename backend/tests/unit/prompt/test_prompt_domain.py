"""
Unit tests for Prompt Domain Layer — Aggregate Root, Entities, Value Objects,
Factory, Specifications, and Domain Services.
"""

from __future__ import annotations

import unittest

from prompt.domain.events.prompt_archived import PromptArchived
from prompt.domain.events.prompt_compiled import PromptCompiled
from prompt.domain.events.prompt_created import PromptCreated
from prompt.domain.events.prompt_published import PromptPublished
from prompt.domain.events.prompt_version_created import PromptVersionCreated
from prompt.domain.factories.prompt_factory import PromptFactory
from prompt.domain.ports.playbook_port import (
    PlaybookDataDTO,
    PlaybookGoalData,
    PlaybookRuleData,
)
from prompt.domain.services.prompt_compilation_service import (
    PromptCompilationService,
)
from prompt.domain.services.prompt_validation_service import (
    PromptValidationService,
)
from prompt.domain.specifications.publishable_prompt_spec import (
    PublishablePromptSpec,
)
from prompt.domain.specifications.valid_prompt_spec import ValidPromptSpec
from prompt.domain.value_objects.prompt_status import PromptStatusType
from shared.kernel.value_objects import WorkspaceId


class TestPromptFactory(unittest.TestCase):
    """Tests for PromptFactory."""

    def test_factory_creates_prompt(self) -> None:
        prompt = PromptFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Sales System Prompt",
            description="B2B sales compiled prompt",
        )

        self.assertEqual(prompt.name, "Sales System Prompt")
        self.assertEqual(prompt.status.value, PromptStatusType.DRAFT)
        self.assertEqual(len(prompt.domain_events), 1)
        self.assertIsInstance(prompt.domain_events[0], PromptCreated)


class TestPromptCompilationService(unittest.TestCase):
    """Tests for PromptCompilationService deterministic compiler."""

    def setUp(self) -> None:
        self.compiler = PromptCompilationService()

    def _make_published_playbook_data(self) -> PlaybookDataDTO:
        return PlaybookDataDTO(
            playbook_id="pb-100",
            version_number=1,
            name="SaaS Sales Playbook",
            description="B2B Sales strategy",
            status="PUBLISHED",
            persona_name="Sarah",
            persona_role="Sales Executive",
            persona_description="Friendly and persuasive",
            tone="PROFESSIONAL",
            formality="SEMI_FORMAL",
            pacing="MODERATE",
            goals=(
                PlaybookGoalData(
                    name="Qualify Lead",
                    description="Check budget & authority",
                    priority=1,
                    is_mandatory=True,
                ),
            ),
            rules=(
                PlaybookRuleData(
                    name="No discounts without approval",
                    condition="discount requested",
                    action="ask manager",
                    is_strict=True,
                ),
            ),
        )

    def test_cannot_compile_draft_playbook(self) -> None:
        playbook_data = PlaybookDataDTO(
            playbook_id="pb-draft",
            version_number=1,
            name="Draft Playbook",
            description="",
            status="DRAFT",
            persona_name="P",
            persona_role="R",
            persona_description="D",
            tone="P",
            formality="F",
            pacing="P",
        )
        res = self.compiler.compile(playbook_data)
        self.assertTrue(res.is_failure)
        self.assertEqual(res.error.code, "INVARIANT_VIOLATION")

    def test_compilation_is_deterministic(self) -> None:
        data = self._make_published_playbook_data()

        res1 = self.compiler.compile(data)
        res2 = self.compiler.compile(data)

        self.assertTrue(res1.is_success)
        self.assertTrue(res2.is_success)

        text1, sections1, meta1 = res1.value
        text2, sections2, meta2 = res2.value

        self.assertEqual(text1, text2)
        self.assertEqual(meta1.checksum, meta2.checksum)
        self.assertIn("Sarah", text1)
        self.assertIn("Qualify Lead", text1)


class TestPromptAggregate(unittest.TestCase):
    """Tests for Prompt Aggregate Root rules and invariants."""

    def setUp(self) -> None:
        self.compiler = PromptCompilationService()
        self.playbook_data = PlaybookDataDTO(
            playbook_id="pb-100",
            version_number=1,
            name="SaaS Sales Playbook",
            description="B2B Sales strategy",
            status="PUBLISHED",
            persona_name="Sarah",
            persona_role="Sales Executive",
            persona_description="Friendly and persuasive",
            tone="PROFESSIONAL",
            formality="SEMI_FORMAL",
            pacing="MODERATE",
            goals=(
                PlaybookGoalData(
                    name="Qualify Lead",
                    description="Check budget & authority",
                    priority=1,
                    is_mandatory=True,
                ),
            ),
        )

    def test_cannot_publish_uncompiled_prompt(self) -> None:
        prompt = PromptFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Draft Prompt",
        )
        res = prompt.publish()
        self.assertTrue(res.is_failure)
        self.assertEqual(res.error.code, "INVALID_STATE")

    def test_successful_compile_and_publish(self) -> None:
        prompt = PromptFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Compiled Prompt",
        )
        prompt.clear_events()

        comp_res = self.compiler.compile(self.playbook_data)
        text, sections, meta = comp_res.value

        set_res = prompt.set_compilation_result(text, sections, meta)
        self.assertTrue(set_res.is_success)
        self.assertEqual(prompt.status.value, PromptStatusType.COMPILED)
        self.assertTrue(any(isinstance(e, PromptCompiled) for e in prompt.domain_events))

        pub_res = prompt.publish(label="v1.0-prod", changelog="Initial prod release")
        self.assertTrue(pub_res.is_success)
        self.assertEqual(prompt.status.value, PromptStatusType.PUBLISHED)
        self.assertEqual(prompt.version_info.version_number, 2)

        events = prompt.domain_events
        self.assertTrue(any(isinstance(e, PromptPublished) for e in events))
        self.assertTrue(any(isinstance(e, PromptVersionCreated) for e in events))

    def test_archive_prompt(self) -> None:
        prompt = PromptFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Archived Prompt",
        )
        prompt.clear_events()

        arch_res = prompt.archive("Obsolete")
        self.assertTrue(arch_res.is_success)
        self.assertEqual(prompt.status.value, PromptStatusType.ARCHIVED)
        self.assertTrue(any(isinstance(e, PromptArchived) for e in prompt.domain_events))


class TestSpecifications(unittest.TestCase):
    """Tests for Prompt specifications."""

    def test_publishable_spec(self) -> None:
        spec = PublishablePromptSpec()
        prompt = PromptFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Test",
        )
        self.assertFalse(spec.is_satisfied_by(prompt))

    def test_valid_spec(self) -> None:
        spec = ValidPromptSpec()
        prompt = PromptFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Valid Prompt",
        )
        self.assertTrue(spec.is_satisfied_by(prompt))


class TestPromptValidationService(unittest.TestCase):
    """Tests for PromptValidationService."""

    def test_service_can_publish(self) -> None:
        svc = PromptValidationService()
        prompt = PromptFactory.create(
            workspace_id=WorkspaceId("ws-1"),
            name="Test",
        )
        self.assertFalse(svc.can_publish(prompt))


if __name__ == "__main__":
    unittest.main()
