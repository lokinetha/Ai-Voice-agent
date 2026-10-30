"""
DeleteDocument Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import DocumentId, KnowledgeBaseId

from knowledge.domain.repositories.knowledge_base_repository import (
    KnowledgeBaseRepository,
)


@dataclass(frozen=True)
class DeleteDocumentCommand(Command):
    """Command requesting Document deletion from KnowledgeBase."""

    kb_id: str
    document_id: str


class DeleteDocumentHandler(CommandHandler[DeleteDocumentCommand, None]):
    """Handler executing DeleteDocumentCommand."""

    def __init__(
        self,
        kb_repository: KnowledgeBaseRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._kb_repo = kb_repository
        self._uow = unit_of_work

    async def handle(self, command: DeleteDocumentCommand) -> Result[None]:
        """Execute Document deletion."""
        kb = await self._kb_repo.get_by_id(KnowledgeBaseId(command.kb_id))
        if kb is None:
            return Result.fail(Error("NOT_FOUND", f"KnowledgeBase '{command.kb_id}' not found"))

        del_res = kb.remove_document(DocumentId(command.document_id))
        if del_res.is_failure:
            return Result.fail(del_res.error)

        async with self._uow:
            await self._kb_repo.save(kb)
            await self._uow.commit()

        return Result.ok(None)
