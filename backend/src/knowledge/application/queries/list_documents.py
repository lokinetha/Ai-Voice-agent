"""
ListDocuments Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import KnowledgeBaseId

from knowledge.application.dto.knowledge_dto import DocumentDTO
from knowledge.application.mappers.knowledge_mapper import KnowledgeMapper
from knowledge.domain.repositories.knowledge_base_repository import (
    KnowledgeBaseRepository,
)


@dataclass(frozen=True)
class ListDocumentsQuery(Query):
    """Query requesting Documents list for a KnowledgeBase."""

    kb_id: str


class ListDocumentsHandler(QueryHandler[ListDocumentsQuery, tuple[DocumentDTO, ...]]):
    """Handler executing ListDocumentsQuery."""

    def __init__(self, kb_repository: KnowledgeBaseRepository) -> None:
        self._kb_repo = kb_repository

    async def handle(self, query: ListDocumentsQuery) -> Result[tuple[DocumentDTO, ...]]:
        """Execute ListDocumentsQuery."""
        if not query.kb_id:
            return Result.fail(Error("VALIDATION_ERROR", "KnowledgeBase ID cannot be empty"))

        kb = await self._kb_repo.get_by_id(KnowledgeBaseId(query.kb_id))
        if kb is None:
            return Result.fail(Error("NOT_FOUND", f"KnowledgeBase with ID '{query.kb_id}' not found"))

        dtos = tuple(KnowledgeMapper.to_document_dto(d, include_chunks=False) for d in kb.documents)
        return Result.ok(dtos)
