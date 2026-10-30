"""
CloneAgent Command and CommandHandler.
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
class CloneAgentCommand(Command):
    """Command requesting Agent cloning."""

    source_agent_id: str
    new_name: str


class CloneAgentHandler(CommandHandler[CloneAgentCommand, AgentDTO]):
    """Handler executing CloneAgentCommand."""

    def __init__(
        self,
        agent_repository: AgentRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._agent_repo = agent_repository
        self._uow = unit_of_work

    async def handle(self, command: CloneAgentCommand) -> Result[AgentDTO]:
        """Execute Agent cloning."""
        if not command.new_name or not command.new_name.strip():
            return Result.fail(Error("VALIDATION_ERROR", "New agent name cannot be empty"))

        source_agent = await self._agent_repo.get_by_id(AgentId(command.source_agent_id))
        if source_agent is None:
            return Result.fail(Error("NOT_FOUND", f"Source Agent '{command.source_agent_id}' not found"))

        # Check unique name invariant within workspace
        existing = await self._agent_repo.get_by_workspace_and_name(
            source_agent.workspace_id, command.new_name.strip()
        )
        if existing is not None:
            return Result.fail(
                Error("CONFLICT", f"An Agent with name '{command.new_name.strip()}' already exists in workspace")
            )

        clone_res = source_agent.clone(new_name=command.new_name.strip())
        if clone_res.is_failure:
            return Result.fail(clone_res.error)

        cloned_agent = clone_res.value

        async with self._uow:
            await self._agent_repo.save(cloned_agent)
            await self._uow.commit()

        return Result.ok(AgentMapper.to_dto(cloned_agent))
