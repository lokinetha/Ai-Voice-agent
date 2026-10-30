"""
Unit tests for Processing Application Command and Query Handlers.
"""

from __future__ import annotations

import asyncio
import unittest
from typing import Self

from processing.application.commands.chunk_document import (
    ChunkDocumentCommand,
    ChunkDocumentHandler,
)
from processing.application.commands.generate_embeddings import (
    GenerateEmbeddingsCommand,
    GenerateEmbeddingsHandler,
)
from processing.application.commands.process_document import (
    ProcessDocumentCommand,
    ProcessDocumentHandler,
)
from processing.application.queries.get_processing_job import (
    GetProcessingJobHandler,
    GetProcessingJobQuery,
)
from processing.application.queries.list_processing_jobs import (
    ListProcessingJobsHandler,
    ListProcessingJobsQuery,
)
from processing.domain.entities.processing_job import ProcessingJob
from processing.domain.repositories.processing_job_repository import (
    ProcessingJobRepository,
)
from processing.infrastructure.adapters.chunking_adapter import ChunkingAdapter
from processing.infrastructure.adapters.embedding_adapter import EmbeddingAdapter
from processing.infrastructure.adapters.object_storage_adapter import (
    ObjectStorageAdapter,
)
from processing.infrastructure.adapters.pdf_parser_adapter import PDFParserAdapter
from processing.infrastructure.adapters.vector_store_adapter import (
    VectorStoreAdapter,
)
from shared.kernel.domain_event import DomainEvent
from shared.kernel.specification import Specification
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import DocumentId, EntityId, WorkspaceId


class InMemoryProcessingJobRepository(ProcessingJobRepository):
    """In-memory test double for ProcessingJobRepository."""

    def __init__(self) -> None:
        self.store: dict[str, ProcessingJob] = {}

    async def get_by_id(self, id: EntityId) -> ProcessingJob | None:
        return self.store.get(str(id.value))

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[ProcessingJob]:
        return [j for j in self.store.values() if j.workspace_id == workspace_id]

    async def find_by_document(self, document_id: DocumentId) -> list[ProcessingJob]:
        return [j for j in self.store.values() if j.document_id == document_id]

    async def save(self, aggregate: ProcessingJob) -> None:
        self.store[str(aggregate.id.value)] = aggregate

    async def delete(self, aggregate: ProcessingJob) -> None:
        self.store.pop(str(aggregate.id.value), None)

    async def find(self, spec: Specification[ProcessingJob]) -> list[ProcessingJob]:
        return [j for j in self.store.values() if spec.is_satisfied_by(j)]

    async def count(self, spec: Specification[ProcessingJob]) -> int:
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


class TestProcessingHandlers(unittest.TestCase):
    """Tests for Processing CQRS Handlers."""

    def setUp(self) -> None:
        self.repo = InMemoryProcessingJobRepository()
        self.uow = DummyUnitOfWork()

        self.storage_adapter = ObjectStorageAdapter()
        self.parser_adapter = PDFParserAdapter()
        self.chunking_adapter = ChunkingAdapter()
        self.embedding_adapter = EmbeddingAdapter()
        self.vector_adapter = VectorStoreAdapter()

    def test_process_document_end_to_end(self) -> None:
        async def run() -> None:
            # Seed storage object
            await self.storage_adapter.store_object(
                bucket="docs",
                key="sample.pdf",
                data=b"Sample PDF document text payload for pipeline testing.",
            )

            handler = ProcessDocumentHandler(
                job_repository=self.repo,
                object_storage_port=self.storage_adapter,
                parser_port=self.parser_adapter,
                chunking_port=self.chunking_adapter,
                embedding_port=self.embedding_adapter,
                vector_store_port=self.vector_adapter,
                unit_of_work=self.uow,
            )

            cmd = ProcessDocumentCommand(
                workspace_id="ws-1",
                document_id="doc-100",
                storage_bucket="docs",
                storage_key="sample.pdf",
                file_type="pdf",
                chunk_size=100,
                chunk_overlap=20,
            )

            res = await handler.handle(cmd)
            self.assertTrue(res.is_success)
            self.assertEqual(res.value.status, "COMPLETED")
            self.assertGreater(len(res.value.chunk_references), 0)
            self.assertGreater(len(res.value.vector_references), 0)

            # Query job
            get_h = GetProcessingJobHandler(self.repo)
            get_res = await get_h.handle(GetProcessingJobQuery(job_id=res.value.id))
            self.assertTrue(get_res.is_success)
            self.assertEqual(get_res.value.id, res.value.id)

        asyncio.run(run())

    def test_chunk_document_handler(self) -> None:
        async def run() -> None:
            handler = ChunkDocumentHandler(self.chunking_adapter)
            cmd = ChunkDocumentCommand(
                text="Line one text. Line two text. Line three text.",
                chunk_size=20,
                chunk_overlap=5,
            )
            res = await handler.handle(cmd)
            self.assertTrue(res.is_success)
            self.assertGreater(len(res.value), 1)

        asyncio.run(run())

    def test_generate_embeddings_handler(self) -> None:
        async def run() -> None:
            handler = GenerateEmbeddingsHandler(self.embedding_adapter)
            cmd = GenerateEmbeddingsCommand(
                texts=("Chunk one text", "Chunk two text"),
                dimension=128,
            )
            res = await handler.handle(cmd)
            self.assertTrue(res.is_success)
            self.assertEqual(len(res.value), 2)
            self.assertEqual(len(res.value[0]), 128)

        asyncio.run(run())

    def test_list_processing_jobs(self) -> None:
        async def run() -> None:
            proc_h = ProcessDocumentHandler(
                self.repo,
                self.storage_adapter,
                self.parser_adapter,
                self.chunking_adapter,
                self.embedding_adapter,
                self.vector_adapter,
                self.uow,
            )
            await proc_h.handle(
                ProcessDocumentCommand(
                    workspace_id="ws-list",
                    document_id="d1",
                    storage_bucket="b",
                    storage_key="k1",
                    file_type="pdf",
                )
            )
            await proc_h.handle(
                ProcessDocumentCommand(
                    workspace_id="ws-list",
                    document_id="d2",
                    storage_bucket="b",
                    storage_key="k2",
                    file_type="pdf",
                )
            )

            list_h = ListProcessingJobsHandler(self.repo)
            list_res = await list_h.handle(ListProcessingJobsQuery(workspace_id="ws-list"))
            self.assertTrue(list_res.is_success)
            self.assertEqual(len(list_res.value), 2)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
