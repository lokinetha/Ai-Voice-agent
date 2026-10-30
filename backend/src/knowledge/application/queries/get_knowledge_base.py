"""
GetKnowledgeBase Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import KnowledgeBaseId

from knowledge.application.dto.knowledge_dto import KnowledgeBaseDTO
from knowledge.application.mappers.knowledge_mapper import KnowledgeMapper
from knowledge.domain.repositories.knowledge_base_repository import (
    KnowledgeBaseRepository,
)


@dataclass(frozen=True)
class GetKnowledgeBaseQuery(Query):
    """Query requesting KnowledgeBase details by kb_id."""

    kb_id: str
    include_documents: bool = True


class GetKnowledgeBaseHandler(QueryHandler[GetKnowledgeBaseQuery, KnowledgeBaseDTO]):
    """Handler executing GetKnowledgeBaseQuery."""

    def __init__(self, kb_repository: KnowledgeBaseRepository) -> None:
        self._kb_repo = kb_repository

    async def handle(self, query: GetKnowledgeBaseQuery) -> Result[KnowledgeBaseDTO]:
        """Execute GetKnowledgeBaseQuery."""
        if not query.kb_id:
            return Result.fail(Error("VALIDATION_ERROR", "KnowledgeBase ID cannot be empty"))

        kb = await self._kb_repo.get_by_id(KnowledgeBaseId(query.kb_id))
        if kb is None:
            return Result.fail(Error("NOT_FOUND", f"KnowledgeBase with ID '{query.kb_id}' not found"))

        return Result.ok(KnowledgeMapper.to_kb_dto(kb, include_documents=query.include_documents))
