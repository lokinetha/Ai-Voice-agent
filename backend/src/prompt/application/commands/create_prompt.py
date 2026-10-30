"""
CreatePrompt Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import WorkspaceId

from prompt.application.dto.prompt_dto import PromptDTO
from prompt.application.mappers.prompt_mapper import PromptMapper
from prompt.domain.factories.prompt_factory import PromptFactory
from prompt.domain.repositories.prompt_repository import PromptRepository


@dataclass(frozen=True)
class CreatePromptCommand(Command):
    """Command requesting Prompt creation."""

    workspace_id: str
    name: str
    description: str = ""


class CreatePromptHandler(CommandHandler[CreatePromptCommand, PromptDTO]):
    """Handler executing CreatePromptCommand."""

    def __init__(
        self,
        prompt_repository: PromptRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = prompt_repository
        self._uow = unit_of_work

    async def handle(self, command: CreatePromptCommand) -> Result[PromptDTO]:
        """Execute Prompt creation."""
        if not command.workspace_id:
            return Result.fail(Error("VALIDATION_ERROR", "Workspace ID cannot be empty"))
        if not command.name or not command.name.strip():
            return Result.fail(Error("VALIDATION_ERROR", "Prompt name cannot be empty"))

        prompt = PromptFactory.create(
            workspace_id=WorkspaceId(command.workspace_id),
            name=command.name,
            description=command.description,
        )

        async with self._uow:
            await self._repo.save(prompt)
            await self._uow.commit()

        return Result.ok(PromptMapper.to_dto(prompt))
