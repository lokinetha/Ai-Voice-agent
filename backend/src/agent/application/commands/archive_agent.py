"""
ArchiveAgent Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import AgentId

from agent.application.dto.agent_dto import AgentDTO
from agent.application.mappers.agent_mapper import AgentMapper
from agent.domain.repositories.agent_repository import AgentRepository


@dataclass(frozen=True)
class ArchiveAgentCommand(Command):
    """Command requesting Agent archiving."""

    agent_id: str


class ArchiveAgentHandler(CommandHandler[ArchiveAgentCommand, AgentDTO]):
    """Handler executing ArchiveAgentCommand."""

    def __init__(
        self,
        agent_repository: AgentRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._agent_repo = agent_repository
        self._uow = unit_of_work

    async def handle(self, command: ArchiveAgentCommand) -> Result[AgentDTO]:
        """Execute Agent archiving."""
        agent = await self._agent_repo.get_by_id(AgentId(command.agent_id))
        if agent is None:
            return Result.fail(Error("NOT_FOUND", f"Agent '{command.agent_id}' not found"))

        archive_res = agent.archive()
        if archive_res.is_failure:
            return Result.fail(archive_res.error)

        async with self._uow:
            await self._agent_repo.save(agent)
            await self._uow.commit()

        return Result.ok(AgentMapper.to_dto(agent))
