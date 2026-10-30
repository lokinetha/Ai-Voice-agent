"""
PublishPrompt Command and CommandHandler.
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
from prompt.domain.services.prompt_validation_service import (
    PromptValidationService,
)


@dataclass(frozen=True)
class PublishPromptCommand(Command):
    """Command requesting Prompt publishing."""

    prompt_id: str
    label: str = ""
    changelog: str = ""


class PublishPromptHandler(CommandHandler[PublishPromptCommand, PromptDTO]):
    """Handler executing PublishPromptCommand."""

    def __init__(
        self,
        prompt_repository: PromptRepository,
        validation_service: PromptValidationService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = prompt_repository
        self._val_svc = validation_service
        self._uow = unit_of_work

    async def handle(self, command: PublishPromptCommand) -> Result[PromptDTO]:
        """Execute Prompt publishing."""
        prompt = await self._repo.get_by_id(PromptId(command.prompt_id))
        if prompt is None:
            return Result.fail(Error("NOT_FOUND", f"Prompt '{command.prompt_id}' not found"))

        if not self._val_svc.can_publish(prompt):
            return Result.fail(
                Error("INVARIANT_VIOLATION", "Prompt is not in a publishable compiled state")
            )

        pub_res = prompt.publish(label=command.label, changelog=command.changelog)
        if pub_res.is_failure:
            return Result.fail(pub_res.error)

        async with self._uow:
            await self._repo.save(prompt)
            await self._uow.commit()

        return Result.ok(PromptMapper.to_dto(prompt))
