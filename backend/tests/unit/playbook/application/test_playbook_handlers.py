"""
Unit tests for Playbook Application Command and Query Handlers.
"""

from __future__ import annotations

import asyncio
import unittest
from typing import Self

from playbook.application.commands.archive_playbook import (
    ArchivePlaybookCommand,
    ArchivePlaybookHandler,
)
from playbook.application.commands.create_playbook import (
    CreatePlaybookCommand,
    CreatePlaybookHandler,
)
from playbook.application.commands.publish_playbook import (
    PublishPlaybookCommand,
    PublishPlaybookHandler,
)
from playbook.application.commands.update_playbook import (
    UpdatePlaybookCommand,
    UpdatePlaybookHandler,
)
from playbook.application.queries.get_playbook import (
    GetPlaybookHandler,
    GetPlaybookQuery,
)
from playbook.application.queries.get_playbook_version import (
    GetPlaybookVersionHandler,
    GetPlaybookVersionQuery,
)
from playbook.application.queries.list_playbooks import (
    ListPlaybooksHandler,
    ListPlaybooksQuery,
)
from playbook.domain.entities.playbook import Playbook
from playbook.domain.entities.playbook_goal import PlaybookGoal
from playbook.domain.repositories.playbook_repository import PlaybookRepository
from playbook.domain.services.playbook_validation_service import (
    PlaybookValidationService,
)
from shared.kernel.domain_event import DomainEvent
from shared.kernel.specification import Specification
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import EntityId, PlaybookId, WorkspaceId


class InMemoryPlaybookRepository(PlaybookRepository):
    """In-memory test double for PlaybookRepository."""

    def __init__(self) -> None:
        self.store: dict[str, Playbook] = {}

    async def get_by_id(self, id: PlaybookId) -> Playbook | None:
        return self.store.get(str(id.value))

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[Playbook]:
        return [p for p in self.store.values() if p.workspace_id == workspace_id]

    async def find_published_version(
        self, playbook_id: PlaybookId, version_number: int
    ) -> Playbook | None:
        pb = self.store.get(str(playbook_id.value))
        if pb and pb.status.is_published and pb.version_info.version_number == version_number:
            return pb
        return None

    async def save(self, aggregate: Playbook) -> None:
        self.store[str(aggregate.id.value)] = aggregate

    async def delete(self, aggregate: Playbook) -> None:
        self.store.pop(str(aggregate.id.value), None)

    async def find(self, spec: Specification[Playbook]) -> list[Playbook]:
        return [p for p in self.store.values() if spec.is_satisfied_by(p)]

    async def count(self, spec: Specification[Playbook]) -> int:
        return len(await self.find(spec))


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


class TestPlaybookHandlers(unittest.TestCase):
    """Tests for Playbook CQRS Handlers."""

    def setUp(self) -> None:
        self.repo = InMemoryPlaybookRepository()
        self.uow = DummyUnitOfWork()
        self.val_svc = PlaybookValidationService()

    def test_create_and_get_playbook(self) -> None:
        async def run() -> None:
            create_h = CreatePlaybookHandler(self.repo, self.uow)
            cmd = CreatePlaybookCommand(
                workspace_id="ws-1",
                name="SaaS Playbook",
                description="B2B sales strategy",
                persona_name="Sarah",
                persona_role="Sales Executive",
            )
            create_res = await create_h.handle(cmd)
            self.assertTrue(create_res.is_success)
            pb_id = create_res.value.id

            get_h = GetPlaybookHandler(self.repo)
            get_res = await get_h.handle(GetPlaybookQuery(playbook_id=pb_id))
            self.assertTrue(get_res.is_success)
            self.assertEqual(get_res.value.name, "SaaS Playbook")
            self.assertIsNotNone(get_res.value.persona)
            self.assertEqual(get_res.value.persona.name, "Sarah")

        asyncio.run(run())

    def test_update_playbook(self) -> None:
        async def run() -> None:
            create_h = CreatePlaybookHandler(self.repo, self.uow)
            create_res = await create_h.handle(
                CreatePlaybookCommand(workspace_id="ws-1", name="Draft Playbook")
            )
            pb_id = create_res.value.id

            update_h = UpdatePlaybookHandler(self.repo, self.uow)
            update_res = await update_h.handle(
                UpdatePlaybookCommand(
                    playbook_id=pb_id,
                    name="Updated Playbook Name",
                    description="New description",
                )
            )
            self.assertTrue(update_res.is_success)
            self.assertEqual(update_res.value.name, "Updated Playbook Name")

        asyncio.run(run())

    def test_publish_and_get_version(self) -> None:
        async def run() -> None:
            create_h = CreatePlaybookHandler(self.repo, self.uow)
            create_res = await create_h.handle(
                CreatePlaybookCommand(
                    workspace_id="ws-1",
                    name="Ready Playbook",
                    persona_name="Sarah",
                    persona_role="Sales Rep",
                )
            )
            pb_id = create_res.value.id

            # Add goal to satisfy publishability
            pb = await self.repo.get_by_id(PlaybookId(pb_id))
            assert pb is not None
            pb.add_goal(PlaybookGoal(id=EntityId(), name="Qualify lead"))
            await self.repo.save(pb)

            pub_h = PublishPlaybookHandler(self.repo, self.val_svc, self.uow)
            pub_res = await pub_h.handle(
                PublishPlaybookCommand(
                    playbook_id=pb_id,
                    label="v1.0",
                    changelog="First official release",
                )
            )
            self.assertTrue(pub_res.is_success)
            self.assertEqual(pub_res.value.status, "PUBLISHED")
            self.assertEqual(pub_res.value.version_info.version_number, 2)

            # Query published version
            ver_h = GetPlaybookVersionHandler(self.repo)
            ver_res = await ver_h.handle(
                GetPlaybookVersionQuery(playbook_id=pb_id, version_number=2)
            )
            self.assertTrue(ver_res.is_success)

        asyncio.run(run())

    def test_archive_playbook(self) -> None:
        async def run() -> None:
            create_h = CreatePlaybookHandler(self.repo, self.uow)
            create_res = await create_h.handle(
                CreatePlaybookCommand(workspace_id="ws-1", name="Old Playbook")
            )
            pb_id = create_res.value.id

            arch_h = ArchivePlaybookHandler(self.repo, self.uow)
            arch_res = await arch_h.handle(
                ArchivePlaybookCommand(playbook_id=pb_id, reason="Obsolete")
            )
            self.assertTrue(arch_res.is_success)
            self.assertEqual(arch_res.value.status, "ARCHIVED")

        asyncio.run(run())

    def test_list_playbooks(self) -> None:
        async def run() -> None:
            create_h = CreatePlaybookHandler(self.repo, self.uow)
            await create_h.handle(
                CreatePlaybookCommand(workspace_id="ws-list", name="Playbook A")
            )
            await create_h.handle(
                CreatePlaybookCommand(workspace_id="ws-list", name="Playbook B")
            )

            list_h = ListPlaybooksHandler(self.repo)
            list_res = await list_h.handle(ListPlaybooksQuery(workspace_id="ws-list"))
            self.assertTrue(list_res.is_success)
            self.assertEqual(len(list_res.value), 2)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
