"""
ArchivePlaybook Command and CommandHandler.
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


@dataclass(frozen=True)
class ArchivePlaybookCommand(Command):
    """Command requesting Playbook archiving."""

    playbook_id: str
    reason: str = ""


class ArchivePlaybookHandler(CommandHandler[ArchivePlaybookCommand, PlaybookDTO]):
    """Handler executing ArchivePlaybookCommand."""

    def __init__(
        self,
        playbook_repository: PlaybookRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = playbook_repository
        self._uow = unit_of_work

    async def handle(self, command: ArchivePlaybookCommand) -> Result[PlaybookDTO]:
        """Execute Playbook archiving."""
        pb = await self._repo.get_by_id(PlaybookId(command.playbook_id))
        if pb is None:
            return Result.fail(Error("NOT_FOUND", f"Playbook '{command.playbook_id}' not found"))

        arch_res = pb.archive(reason=command.reason)
        if arch_res.is_failure:
            return Result.fail(arch_res.error)

        async with self._uow:
            await self._repo.save(pb)
            await self._uow.commit()

        return Result.ok(PlaybookMapper.to_dto(pb))
