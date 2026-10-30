"""
CreateKnowledgeBase Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import WorkspaceId

from knowledge.application.dto.knowledge_dto import KnowledgeBaseDTO
from knowledge.application.mappers.knowledge_mapper import KnowledgeMapper
from knowledge.domain.factories.knowledge_base_factory import KnowledgeBaseFactory
from knowledge.domain.repositories.knowledge_base_repository import (
    KnowledgeBaseRepository,
)
from knowledge.domain.value_objects.retrieval_policy import RetrievalPolicy


@dataclass(frozen=True)
class CreateKnowledgeBaseCommand(Command):
    """Command requesting KnowledgeBase creation."""

    workspace_id: str
    name: str
    description: str = ""
    top_k: int = 5
    similarity_threshold: float = 0.7
    strategy: str = "hybrid"


class CreateKnowledgeBaseHandler(CommandHandler[CreateKnowledgeBaseCommand, KnowledgeBaseDTO]):
    """Handler executing CreateKnowledgeBaseCommand."""

    def __init__(
        self,
        kb_repository: KnowledgeBaseRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._kb_repo = kb_repository
        self._uow = unit_of_work

    async def handle(self, command: CreateKnowledgeBaseCommand) -> Result[KnowledgeBaseDTO]:
        """Execute KnowledgeBase creation."""
        if not command.name or not command.name.strip():
            return Result.fail(Error("VALIDATION_ERROR", "KnowledgeBase name cannot be empty"))

        ws_id = WorkspaceId(command.workspace_id)

        existing = await self._kb_repo.get_by_workspace_and_name(ws_id, command.name.strip())
        if existing is not None:
            return Result.fail(
                Error(
                    "CONFLICT",
                    f"A KnowledgeBase with name '{command.name.strip()}' already exists in workspace",
                )
            )

        try:
            policy = RetrievalPolicy(
                top_k=command.top_k,
                similarity_threshold=command.similarity_threshold,
                strategy=command.strategy,
            )
        except ValueError as err:
            return Result.fail(Error("VALIDATION_ERROR", str(err)))

        kb = KnowledgeBaseFactory.create(
            workspace_id=ws_id,
            name=command.name,
            description=command.description,
            retrieval_policy=policy,
        )

        async with self._uow:
            await self._kb_repo.save(kb)
            await self._uow.commit()

        return Result.ok(KnowledgeMapper.to_kb_dto(kb))
