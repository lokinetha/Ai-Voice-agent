"""
ReindexKnowledgeBase Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import KnowledgeBaseId

from knowledge.application.dto.knowledge_dto import KnowledgeBaseDTO
from knowledge.application.mappers.knowledge_mapper import KnowledgeMapper
from knowledge.domain.repositories.knowledge_base_repository import (
    KnowledgeBaseRepository,
)
from knowledge.domain.services.knowledge_base_indexing_service import (
    KnowledgeBaseIndexingService,
)


@dataclass(frozen=True)
class ReindexKnowledgeBaseCommand(Command):
    """Command requesting KnowledgeBase reindexing."""

    kb_id: str


class ReindexKnowledgeBaseHandler(CommandHandler[ReindexKnowledgeBaseCommand, KnowledgeBaseDTO]):
    """Handler executing ReindexKnowledgeBaseCommand."""

    def __init__(
        self,
        kb_repository: KnowledgeBaseRepository,
        indexing_service: KnowledgeBaseIndexingService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._kb_repo = kb_repository
        self._indexing_service = indexing_service
        self._uow = unit_of_work

    async def handle(self, command: ReindexKnowledgeBaseCommand) -> Result[KnowledgeBaseDTO]:
        """Execute KnowledgeBase reindexing initiation."""
        kb = await self._kb_repo.get_by_id(KnowledgeBaseId(command.kb_id))
        if kb is None:
            return Result.fail(Error("NOT_FOUND", f"KnowledgeBase '{command.kb_id}' not found"))

        reindex_res = self._indexing_service.validate_and_reindex(kb)
        if reindex_res.is_failure:
            return Result.fail(reindex_res.error)

        async with self._uow:
            await self._kb_repo.save(kb)
            await self._uow.commit()

        return Result.ok(KnowledgeMapper.to_kb_dto(kb))
