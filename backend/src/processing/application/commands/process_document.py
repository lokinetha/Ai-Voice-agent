"""
ProcessDocument Command and CommandHandler.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import DocumentId, WorkspaceId

from processing.application.dto.processing_dto import ProcessingJobDTO
from processing.application.mappers.processing_job_mapper import (
    ProcessingJobMapper,
)
from processing.domain.factories.processing_job_factory import (
    ProcessingJobFactory,
)
from processing.domain.ports.chunking_port import ChunkingPort
from processing.domain.ports.document_parser_port import DocumentParserPort
from processing.domain.ports.embedding_port import EmbeddingPort
from processing.domain.ports.object_storage_port import ObjectStoragePort
from processing.domain.ports.vector_store_port import VectorStorePort
from processing.domain.repositories.processing_job_repository import (
    ProcessingJobRepository,
)
from processing.domain.value_objects.chunking_strategy import ChunkingStrategy
from processing.domain.value_objects.embedding_strategy import EmbeddingStrategy
from processing.domain.value_objects.processing_result import ProcessingResult
from processing.domain.value_objects.processing_task_type import TaskCategory


@dataclass(frozen=True)
class ProcessDocumentCommand(Command):
    """Command requesting full end-to-end document processing pipeline execution."""

    workspace_id: str
    document_id: str
    storage_bucket: str
    storage_key: str
    file_type: str
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_model: str = "standard-text-embedding"


class ProcessDocumentHandler(CommandHandler[ProcessDocumentCommand, ProcessingJobDTO]):
    """Handler executing the full document processing pipeline via ports."""

    def __init__(
        self,
        job_repository: ProcessingJobRepository,
        object_storage_port: ObjectStoragePort,
        parser_port: DocumentParserPort,
        chunking_port: ChunkingPort,
        embedding_port: EmbeddingPort,
        vector_store_port: VectorStorePort,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = job_repository
        self._storage = object_storage_port
        self._parser = parser_port
        self._chunking = chunking_port
        self._embedding = embedding_port
        self._vector_store = vector_store_port
        self._uow = unit_of_work

    async def handle(self, command: ProcessDocumentCommand) -> Result[ProcessingJobDTO]:
        """Execute end-to-end document processing pipeline."""
        if not command.workspace_id or not command.document_id:
            return Result.fail(Error("VALIDATION_ERROR", "workspace_id and document_id required"))

        chunking_strat = ChunkingStrategy(
            chunk_size=command.chunk_size,
            chunk_overlap=command.chunk_overlap,
        )
        embedding_strat = EmbeddingStrategy(model_name=command.embedding_model)

        job = ProcessingJobFactory.create(
            workspace_id=WorkspaceId(command.workspace_id),
            document_id=DocumentId(command.document_id),
            chunking_strategy=chunking_strat,
            embedding_strategy=embedding_strat,
        )

        job.start()

        try:
            # 1. Fetch & Parse Document
            t0 = time.time()
            file_bytes = await self._storage.fetch_object(
                command.storage_bucket, command.storage_key
            )
            raw_text = await self._parser.parse_document(file_bytes, command.file_type)
            parse_time = time.time() - t0

            job.complete_task(
                TaskCategory.PARSING,
                ProcessingResult(
                    output_count=1,
                    execution_time_seconds=parse_time,
                    metadata={"character_count": len(raw_text)},
                ),
            )

            # 2. Chunk Text
            t0 = time.time()
            chunks = await self._chunking.chunk_text(raw_text, chunking_strat)
            chunk_time = time.time() - t0

            chunk_refs = [f"chunk-{i+1}" for i in range(len(chunks))]

            job.complete_task(
                TaskCategory.CHUNKING,
                ProcessingResult(
                    output_count=len(chunks),
                    execution_time_seconds=chunk_time,
                    metadata={"chunk_references": chunk_refs},
                ),
            )

            # 3. Generate Embeddings
            t0 = time.time()
            vectors = await self._embedding.generate_embeddings(chunks, embedding_strat)
            embed_time = time.time() - t0

            job.complete_task(
                TaskCategory.EMBEDDING,
                ProcessingResult(
                    output_count=len(vectors),
                    execution_time_seconds=embed_time,
                    metadata={"dimension": embedding_strat.dimension},
                ),
            )

            # 4. Index in Vector Store
            t0 = time.time()
            payloads = [
                {"document_id": command.document_id, "chunk_ref": chunk_refs[i], "text": chunks[i]}
                for i in range(len(chunks))
            ]
            vector_refs = await self._vector_store.store_vectors(
                collection_name=f"workspace-{command.workspace_id}",
                vectors=vectors,
                payloads=payloads,
            )
            index_time = time.time() - t0

            job.complete_task(
                TaskCategory.INDEXING,
                ProcessingResult(
                    output_count=len(vector_refs),
                    execution_time_seconds=index_time,
                    metadata={"vector_references": vector_refs},
                ),
            )

            job.complete_job(chunk_refs=chunk_refs, vector_refs=vector_refs)

        except Exception as err:
            job.fail_job(str(err))

        async with self._uow:
            await self._repo.save(job)
            await self._uow.commit()

        return Result.ok(ProcessingJobMapper.to_dto(job))
