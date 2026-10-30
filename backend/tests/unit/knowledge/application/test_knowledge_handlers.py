"""
Unit tests for Knowledge Application Command and Query Handlers.
"""

from __future__ import annotations

import asyncio
import unittest
from typing import Self

from knowledge.application.commands.create_knowledge_base import (
    CreateKnowledgeBaseCommand,
    CreateKnowledgeBaseHandler,
)
from knowledge.application.commands.delete_document import (
    DeleteDocumentCommand,
    DeleteDocumentHandler,
)
from knowledge.application.commands.reindex_knowledge_base import (
    ReindexKnowledgeBaseCommand,
    ReindexKnowledgeBaseHandler,
)
from knowledge.application.commands.upload_document import (
    UploadDocumentCommand,
    UploadDocumentHandler,
)
from knowledge.application.queries.list_documents import (
    ListDocumentsHandler,
    ListDocumentsQuery,
)
from knowledge.application.queries.search_metadata import (
    SearchMetadataHandler,
    SearchMetadataQuery,
)
from knowledge.domain.entities.knowledge_base import KnowledgeBase
from knowledge.domain.repositories.knowledge_base_repository import (
    KnowledgeBaseRepository,
)
from knowledge.domain.services.knowledge_base_indexing_service import (
    KnowledgeBaseIndexingService,
)
from shared.kernel.domain_event import DomainEvent
from shared.kernel.specification import Specification
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import KnowledgeBaseId, WorkspaceId


class InMemoryKnowledgeBaseRepository(KnowledgeBaseRepository):
    def __init__(self) -> None:
        self.kbs: dict[str, KnowledgeBase] = {}

    async def get_by_id(self, id: KnowledgeBaseId) -> KnowledgeBase | None:
        return self.kbs.get(str(id.value))

    async def get_by_workspace_and_name(
        self, workspace_id: WorkspaceId, name: str
    ) -> KnowledgeBase | None:
        for kb in self.kbs.values():
            if kb.workspace_id == workspace_id and kb.name.lower() == name.strip().lower():
                return kb
        return None

    async def find_by_workspace(
        self, workspace_id: WorkspaceId
    ) -> list[KnowledgeBase]:
        return [kb for kb in self.kbs.values() if kb.workspace_id == workspace_id]

    async def save(self, aggregate: KnowledgeBase) -> None:
        self.kbs[str(aggregate.id.value)] = aggregate

    async def delete(self, aggregate: KnowledgeBase) -> None:
        self.kbs.pop(str(aggregate.id.value), None)

    async def find(self, spec: Specification[KnowledgeBase]) -> list[KnowledgeBase]:
        return [kb for kb in self.kbs.values() if spec.is_satisfied_by(kb)]

    async def count(self, spec: Specification[KnowledgeBase]) -> int:
        return len(await self.find(spec))


class DummyUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object | None) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass

    def collect_events(self) -> list[DomainEvent]:
        return []


class TestKnowledgeApplicationHandlers(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryKnowledgeBaseRepository()
        self.uow = DummyUnitOfWork()
        self.indexing_svc = KnowledgeBaseIndexingService()

    def test_create_knowledge_base_success(self) -> None:
        async def run() -> None:
            handler = CreateKnowledgeBaseHandler(self.repo, self.uow)
            cmd = CreateKnowledgeBaseCommand(
                workspace_id="ws-kb-test",
                name="Sales SOPs",
                description="Standard Operating Procedures",
            )
            res = await handler.handle(cmd)
            self.assertTrue(res.is_success)
            self.assertEqual(res.value.name, "Sales SOPs")
            self.assertEqual(res.value.workspace_id, "ws-kb-test")

        asyncio.run(run())

    def test_upload_and_list_documents(self) -> None:
        async def run() -> None:
            create_h = CreateKnowledgeBaseHandler(self.repo, self.uow)
            kb_res = await create_h.handle(
                CreateKnowledgeBaseCommand(workspace_id="ws-kb-test", name="Tech Specs")
            )
            kb_id = kb_res.value.id

            upload_h = UploadDocumentHandler(self.repo, self.uow)
            doc_res = await upload_h.handle(
                UploadDocumentCommand(
                    kb_id=kb_id,
                    file_name="architecture_overview.pdf",
                    file_type="pdf",
                    size_bytes=51200,
                    tags={"author": "alice"},
                )
            )
            self.assertTrue(doc_res.is_success)
            self.assertEqual(doc_res.value.file_name, "architecture_overview.pdf")

            list_h = ListDocumentsHandler(self.repo)
            docs_res = await list_h.handle(ListDocumentsQuery(kb_id=kb_id))
            self.assertTrue(docs_res.is_success)
            self.assertEqual(len(docs_res.value), 1)

            # Metadata search query
            search_h = SearchMetadataHandler(self.repo)
            search_res = await search_h.handle(
                SearchMetadataQuery(kb_id=kb_id, tag_key="author", tag_value="alice")
            )
            self.assertTrue(search_res.is_success)
            self.assertEqual(len(search_res.value), 1)

        asyncio.run(run())

    def test_reindex_and_delete_document_handlers(self) -> None:
        async def run() -> None:
            create_h = CreateKnowledgeBaseHandler(self.repo, self.uow)
            kb_res = await create_h.handle(
                CreateKnowledgeBaseCommand(workspace_id="ws-kb-test", name="Reindex Target KB")
            )
            kb_id = kb_res.value.id

            upload_h = UploadDocumentHandler(self.repo, self.uow)
            doc_res = await upload_h.handle(
                UploadDocumentCommand(kb_id=kb_id, file_name="doc1.pdf", file_type="pdf", size_bytes=1000)
            )

            reindex_h = ReindexKnowledgeBaseHandler(self.repo, self.indexing_svc, self.uow)
            reindex_res = await reindex_h.handle(ReindexKnowledgeBaseCommand(kb_id=kb_id))
            self.assertTrue(reindex_res.is_success)
            self.assertEqual(reindex_res.value.status, "INDEXING")

            del_h = DeleteDocumentHandler(self.repo, self.uow)
            del_res = await del_h.handle(DeleteDocumentCommand(kb_id=kb_id, document_id=doc_res.value.id))
            self.assertTrue(del_res.is_success)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
