"""
UpdatePlaybook Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import PlaybookId

from playbook.application.dto.playbook_dto import PlaybookDTO
from playbook.application.mappers.playbook_mapper import PlaybookMapper
from playbook.domain.repositories.playbook_repository import PlaybookRepository
from playbook.domain.value_objects.persona import Persona


@dataclass(frozen=True)
class UpdatePlaybookCommand(Command):
    """Command requesting Playbook update."""

    playbook_id: str
    name: str
    description: str = ""
    persona_name: str = ""
    persona_role: str = ""
    persona_description: str = ""
    persona_industry: str = ""


class UpdatePlaybookHandler(CommandHandler[UpdatePlaybookCommand, PlaybookDTO]):
    """Handler executing UpdatePlaybookCommand."""

    def __init__(
        self,
        playbook_repository: PlaybookRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = playbook_repository
        self._uow = unit_of_work

    async def handle(self, command: UpdatePlaybookCommand) -> Result[PlaybookDTO]:
        """Execute Playbook update."""
        pb = await self._repo.get_by_id(PlaybookId(command.playbook_id))
        if pb is None:
            return Result.fail(Error("NOT_FOUND", f"Playbook '{command.playbook_id}' not found"))

        meta_res = pb.update_metadata(command.name, command.description)
        if meta_res.is_failure:
            return Result.fail(meta_res.error)

        if command.persona_name and command.persona_role:
            try:
                persona = Persona(
                    name=command.persona_name,
                    role=command.persona_role,
                    description=command.persona_description,
                    industry=command.persona_industry,
                )
                persona_res = pb.set_persona(persona)
                if persona_res.is_failure:
                    return Result.fail(persona_res.error)
            except ValueError as err:
                return Result.fail(Error("VALIDATION_ERROR", str(err)))

        async with self._uow:
            await self._repo.save(pb)
            await self._uow.commit()

        return Result.ok(PlaybookMapper.to_dto(pb))
