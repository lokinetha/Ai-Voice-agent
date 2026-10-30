"""
UpdatePrompt Command and CommandHandler.
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
class UpdatePromptCommand(Command):
    """Command requesting Prompt metadata update."""

    prompt_id: str
    name: str
    description: str = ""


class UpdatePromptHandler(CommandHandler[UpdatePromptCommand, PromptDTO]):
    """Handler executing UpdatePromptCommand."""

    def __init__(
        self,
        prompt_repository: PromptRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = prompt_repository
        self._uow = unit_of_work

    async def handle(self, command: UpdatePromptCommand) -> Result[PromptDTO]:
        """Execute Prompt metadata update."""
        prompt = await self._repo.get_by_id(PromptId(command.prompt_id))
        if prompt is None:
            return Result.fail(Error("NOT_FOUND", f"Prompt '{command.prompt_id}' not found"))

        upd_res = prompt.update_metadata(command.name, command.description)
        if upd_res.is_failure:
            return Result.fail(upd_res.error)

        async with self._uow:
            await self._repo.save(prompt)
            await self._uow.commit()

        return Result.ok(PromptMapper.to_dto(prompt))
