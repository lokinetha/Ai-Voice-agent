"""
UploadDocument Command and CommandHandler.

Registers a new Document record and its metadata within a KnowledgeBase.
Does NOT run embeddings or LLMs (delegated to Processing context).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import DocumentId, KnowledgeBaseId

from knowledge.application.dto.knowledge_dto import DocumentDTO
from knowledge.application.mappers.knowledge_mapper import KnowledgeMapper
from knowledge.domain.entities.document import Document
from knowledge.domain.repositories.knowledge_base_repository import (
    KnowledgeBaseRepository,
)
from knowledge.domain.value_objects.document_metadata import DocumentMetadata


@dataclass(frozen=True)
class UploadDocumentCommand(Command):
    """Command requesting document upload metadata registration."""

    kb_id: str
    file_name: str
    file_type: str
    size_bytes: int
    source_url: str | None = None
    tags: dict[str, Any] | None = None


class UploadDocumentHandler(CommandHandler[UploadDocumentCommand, DocumentDTO]):
    """Handler executing UploadDocumentCommand."""

    def __init__(
        self,
        kb_repository: KnowledgeBaseRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._kb_repo = kb_repository
        self._uow = unit_of_work

    async def handle(self, command: UploadDocumentCommand) -> Result[DocumentDTO]:
        """Execute document registration."""
        kb = await self._kb_repo.get_by_id(KnowledgeBaseId(command.kb_id))
        if kb is None:
            return Result.fail(Error("NOT_FOUND", f"KnowledgeBase '{command.kb_id}' not found"))

        try:
            meta = DocumentMetadata.create(
                file_type=command.file_type,
                size_bytes=command.size_bytes,
                source_url=command.source_url,
                tags=command.tags,
            )
        except ValueError as err:
            return Result.fail(Error("VALIDATION_ERROR", str(err)))

        doc_id = DocumentId()
        doc = Document(
            id=doc_id,
            file_name=command.file_name,
            metadata=meta,
        )

        add_res = kb.add_document(doc)
        if add_res.is_failure:
            return Result.fail(add_res.error)

        async with self._uow:
            await self._kb_repo.save(kb)
            await self._uow.commit()

        return Result.ok(KnowledgeMapper.to_document_dto(doc))
