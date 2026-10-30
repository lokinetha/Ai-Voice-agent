"""
CreatePromptVersion Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import PromptId

from prompt.application.dto.prompt_dto import PromptDTO
from prompt.application.mappers.prompt_mapper import PromptMapper
from prompt.domain.repositories.prompt_repository import PromptRepository


@dataclass(frozen=True)
class CreatePromptVersionCommand(Command):
    """Command requesting explicit creation of a published Prompt version snapshot."""

    prompt_id: str
    label: str = ""
    changelog: str = ""


class CreatePromptVersionHandler(CommandHandler[CreatePromptVersionCommand, PromptDTO]):
    """Handler executing CreatePromptVersionCommand."""

    def __init__(
        self,
        prompt_repository: PromptRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = prompt_repository
        self._uow = unit_of_work

    async def handle(self, command: CreatePromptVersionCommand) -> Result[PromptDTO]:
        """Execute Prompt version snapshot creation."""
        prompt = await self._repo.get_by_id(PromptId(command.prompt_id))
        if prompt is None:
            return Result.fail(Error("NOT_FOUND", f"Prompt '{command.prompt_id}' not found"))

        pub_res = prompt.publish(label=command.label, changelog=command.changelog)
        if pub_res.is_failure:
            return Result.fail(pub_res.error)

        async with self._uow:
            await self._repo.save(prompt)
            await self._uow.commit()

        return Result.ok(PromptMapper.to_dto(prompt))
