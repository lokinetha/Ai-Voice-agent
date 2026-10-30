"""
Unit tests for Prompt Application Command and Query Handlers.
"""

from __future__ import annotations

import asyncio
import unittest
from typing import Self

from prompt.application.commands.archive_prompt import (
    ArchivePromptCommand,
    ArchivePromptHandler,
)
from prompt.application.commands.compile_prompt import (
    CompilePromptCommand,
    CompilePromptHandler,
)
from prompt.application.commands.create_prompt import (
    CreatePromptCommand,
    CreatePromptHandler,
)
from prompt.application.commands.publish_prompt import (
    PublishPromptCommand,
    PublishPromptHandler,
)
from prompt.application.commands.update_prompt import (
    UpdatePromptCommand,
    UpdatePromptHandler,
)
from prompt.application.queries.get_prompt import (
    GetPromptHandler,
    GetPromptQuery,
)
from prompt.application.queries.get_prompt_version import (
    GetPromptVersionHandler,
    GetPromptVersionQuery,
)
from prompt.application.queries.list_prompts import (
    ListPromptsHandler,
    ListPromptsQuery,
)
from prompt.domain.entities.prompt import Prompt
from prompt.domain.ports.playbook_port import (
    PlaybookDataDTO,
    PlaybookGoalData,
    PlaybookQueryPort,
)
from prompt.domain.repositories.prompt_repository import PromptRepository
from prompt.domain.services.prompt_compilation_service import (
    PromptCompilationService,
)
from prompt.domain.services.prompt_validation_service import (
    PromptValidationService,
)
from shared.kernel.domain_event import DomainEvent
from shared.kernel.specification import Specification
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import PromptId, WorkspaceId


class InMemoryPromptRepository(PromptRepository):
    """In-memory test double for PromptRepository."""

    def __init__(self) -> None:
        self.store: dict[str, Prompt] = {}

    async def get_by_id(self, id: PromptId) -> Prompt | None:
        return self.store.get(str(id.value))

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[Prompt]:
        return [p for p in self.store.values() if p.workspace_id == workspace_id]

    async def find_published_version(
        self, prompt_id: PromptId, version_number: int
    ) -> Prompt | None:
        p = self.store.get(str(prompt_id.value))
        if p and p.status.is_published and p.version_info.version_number == version_number:
            return p
        return None

    async def save(self, aggregate: Prompt) -> None:
        self.store[str(aggregate.id.value)] = aggregate

    async def delete(self, aggregate: Prompt) -> None:
        self.store.pop(str(aggregate.id.value), None)

    async def find(self, spec: Specification[Prompt]) -> list[Prompt]:
        return [p for p in self.store.values() if spec.is_satisfied_by(p)]

    async def count(self, spec: Specification[Prompt]) -> int:
        return len(await self.find(spec))


class MockPlaybookQueryPort(PlaybookQueryPort):
    """Test double for PlaybookQueryPort."""

    def __init__(self, data_map: dict[str, PlaybookDataDTO] | None = None) -> None:
        self.data_map = data_map or {}

    async def get_published_playbook(
        self, playbook_id: str, version_number: int | None = None
    ) -> PlaybookDataDTO | None:
        return self.data_map.get(playbook_id)


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


class TestPromptHandlers(unittest.TestCase):
    """Tests for Prompt CQRS Handlers."""

    def setUp(self) -> None:
        self.repo = InMemoryPromptRepository()
        self.uow = DummyUnitOfWork()
        self.comp_svc = PromptCompilationService()
        self.val_svc = PromptValidationService()

        self.sample_playbook = PlaybookDataDTO(
            playbook_id="pb-pub-1",
            version_number=1,
            name="Published Sales Playbook",
            description="B2B sales strategy",
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
        self.playbook_port = MockPlaybookQueryPort({"pb-pub-1": self.sample_playbook})

    def test_create_and_get_prompt(self) -> None:
        async def run() -> None:
            create_h = CreatePromptHandler(self.repo, self.uow)
            create_res = await create_h.handle(
                CreatePromptCommand(
                    workspace_id="ws-1",
                    name="Sales Prompt",
                    description="Compiled system prompt for sales agent",
                )
            )
            self.assertTrue(create_res.is_success)
            p_id = create_res.value.id

            get_h = GetPromptHandler(self.repo)
            get_res = await get_h.handle(GetPromptQuery(prompt_id=p_id))
            self.assertTrue(get_res.is_success)
            self.assertEqual(get_res.value.name, "Sales Prompt")

        asyncio.run(run())

    def test_compile_and_publish_prompt(self) -> None:
        async def run() -> None:
            create_h = CreatePromptHandler(self.repo, self.uow)
            create_res = await create_h.handle(
                CreatePromptCommand(workspace_id="ws-1", name="Prompt to Compile")
            )
            p_id = create_res.value.id

            comp_h = CompilePromptHandler(
                self.repo, self.playbook_port, self.comp_svc, self.uow
            )
            comp_res = await comp_h.handle(
                CompilePromptCommand(prompt_id=p_id, playbook_id="pb-pub-1")
            )
            self.assertTrue(comp_res.is_success)
            self.assertEqual(comp_res.value.status, "COMPILED")
            self.assertIn("Sarah", comp_res.value.compiled_prompt_text)

            pub_h = PublishPromptHandler(self.repo, self.val_svc, self.uow)
            pub_res = await pub_h.handle(
                PublishPromptCommand(prompt_id=p_id, label="v1.0", changelog="Initial compile")
            )
            self.assertTrue(pub_res.is_success)
            self.assertEqual(pub_res.value.status, "PUBLISHED")

            ver_h = GetPromptVersionHandler(self.repo)
            ver_res = await ver_h.handle(
                GetPromptVersionQuery(prompt_id=p_id, version_number=2)
            )
            self.assertTrue(ver_res.is_success)

        asyncio.run(run())

    def test_update_and_archive_prompt(self) -> None:
        async def run() -> None:
            create_h = CreatePromptHandler(self.repo, self.uow)
            create_res = await create_h.handle(
                CreatePromptCommand(workspace_id="ws-1", name="Draft Prompt")
            )
            p_id = create_res.value.id

            upd_h = UpdatePromptHandler(self.repo, self.uow)
            upd_res = await upd_h.handle(
                UpdatePromptCommand(
                    prompt_id=p_id, name="Updated Prompt", description="New desc"
                )
            )
            self.assertTrue(upd_res.is_success)
            self.assertEqual(upd_res.value.name, "Updated Prompt")

            arch_h = ArchivePromptHandler(self.repo, self.uow)
            arch_res = await arch_h.handle(
                ArchivePromptCommand(prompt_id=p_id, reason="Obsolete")
            )
            self.assertTrue(arch_res.is_success)
            self.assertEqual(arch_res.value.status, "ARCHIVED")

        asyncio.run(run())

    def test_list_prompts(self) -> None:
        async def run() -> None:
            create_h = CreatePromptHandler(self.repo, self.uow)
            await create_h.handle(
                CreatePromptCommand(workspace_id="ws-list", name="Prompt A")
            )
            await create_h.handle(
                CreatePromptCommand(workspace_id="ws-list", name="Prompt B")
            )

            list_h = ListPromptsHandler(self.repo)
            list_res = await list_h.handle(ListPromptsQuery(workspace_id="ws-list"))
            self.assertTrue(list_res.is_success)
            self.assertEqual(len(list_res.value), 2)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
