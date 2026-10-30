"""
SearchMetadata Query and QueryHandler.

Performs metadata and tag filtering over document records.
Does NOT execute vector search or LLM generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import KnowledgeBaseId

from knowledge.application.dto.knowledge_dto import DocumentDTO
from knowledge.application.mappers.knowledge_mapper import KnowledgeMapper
from knowledge.domain.repositories.knowledge_base_repository import (
    KnowledgeBaseRepository,
)


@dataclass(frozen=True)
class SearchMetadataQuery(Query):
    """Query filtering documents by file_type or metadata tags."""

    kb_id: str
    file_type: str | None = None
    tag_key: str | None = None
    tag_value: Any | None = None


class SearchMetadataHandler(QueryHandler[SearchMetadataQuery, tuple[DocumentDTO, ...]]):
    """Handler executing SearchMetadataQuery."""

    def __init__(self, kb_repository: KnowledgeBaseRepository) -> None:
        self._kb_repo = kb_repository

    async def handle(self, query: SearchMetadataQuery) -> Result[tuple[DocumentDTO, ...]]:
        """Execute SearchMetadataQuery."""
        if not query.kb_id:
            return Result.fail(Error("VALIDATION_ERROR", "KnowledgeBase ID cannot be empty"))

        kb = await self._kb_repo.get_by_id(KnowledgeBaseId(query.kb_id))
        if kb is None:
            return Result.fail(Error("NOT_FOUND", f"KnowledgeBase with ID '{query.kb_id}' not found"))

        matching_docs = []
        for doc in kb.documents:
            if query.file_type and doc.metadata.file_type.lower() != query.file_type.lower():
                continue
            if query.tag_key:
                if query.tag_key not in doc.metadata.tags:
                    continue
                if query.tag_value is not None and doc.metadata.tags[query.tag_key] != query.tag_value:
                    continue
            matching_docs.append(doc)

        dtos = tuple(KnowledgeMapper.to_document_dto(d) for d in matching_docs)
        return Result.ok(dtos)
