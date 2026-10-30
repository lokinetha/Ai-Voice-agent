"""
PublishPlaybook Command and CommandHandler.
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
from playbook.domain.services.playbook_validation_service import (
    PlaybookValidationService,
)


@dataclass(frozen=True)
class PublishPlaybookCommand(Command):
    """Command requesting Playbook publishing."""

    playbook_id: str
    label: str = ""
    changelog: str = ""


class PublishPlaybookHandler(CommandHandler[PublishPlaybookCommand, PlaybookDTO]):
    """Handler executing PublishPlaybookCommand."""

    def __init__(
        self,
        playbook_repository: PlaybookRepository,
        validation_service: PlaybookValidationService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = playbook_repository
        self._val_svc = validation_service
        self._uow = unit_of_work

    async def handle(self, command: PublishPlaybookCommand) -> Result[PlaybookDTO]:
        """Execute Playbook publishing."""
        pb = await self._repo.get_by_id(PlaybookId(command.playbook_id))
        if pb is None:
            return Result.fail(Error("NOT_FOUND", f"Playbook '{command.playbook_id}' not found"))

        if not self._val_svc.can_publish(pb):
            return Result.fail(
                Error("INVARIANT_VIOLATION", "Playbook does not satisfy publishability requirements")
            )

        pub_res = pb.publish(label=command.label, changelog=command.changelog)
        if pub_res.is_failure:
            return Result.fail(pub_res.error)

        async with self._uow:
            await self._repo.save(pb)
            await self._uow.commit()

        return Result.ok(PlaybookMapper.to_dto(pb))
