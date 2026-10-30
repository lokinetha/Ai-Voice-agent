"""
CreateAgent Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import WorkspaceId

from agent.application.dto.agent_dto import AgentDTO
from agent.application.mappers.agent_mapper import AgentMapper
from agent.domain.factories.agent_factory import AgentFactory
from agent.domain.repositories.agent_repository import AgentRepository
from agent.domain.value_objects.agent_type import AgentCategory, AgentType


@dataclass(frozen=True)
class CreateAgentCommand(Command):
    """Command requesting new Agent aggregate creation."""

    workspace_id: str
    name: str
    agent_type: str = "SALES"


class CreateAgentHandler(CommandHandler[CreateAgentCommand, AgentDTO]):
    """Handler executing CreateAgentCommand."""

    def __init__(
        self,
        agent_repository: AgentRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._agent_repo = agent_repository
        self._uow = unit_of_work

    async def handle(self, command: CreateAgentCommand) -> Result[AgentDTO]:
        """Execute Agent creation while enforcing workspace name uniqueness invariant.

        Args:
            command: CreateAgentCommand instance.

        Returns:
            Result wrapping AgentDTO on success, or Error on failure.
        """
        if not command.name or not command.name.strip():
            return Result.fail(Error("VALIDATION_ERROR", "Agent name cannot be empty"))

        ws_id = WorkspaceId(command.workspace_id)

        # Invariant check: Agent name must be unique within a Workspace
        existing = await self._agent_repo.get_by_workspace_and_name(ws_id, command.name.strip())
        if existing is not None:
            return Result.fail(
                Error(
                    "CONFLICT",
                    f"An Agent with name '{command.name.strip()}' already exists in workspace {command.workspace_id}",
                )
            )

        try:
            a_type = AgentType(AgentCategory(command.agent_type.upper()))
        except ValueError:
            return Result.fail(Error("VALIDATION_ERROR", f"Invalid agent_type: {command.agent_type}"))

        agent = AgentFactory.create(
            workspace_id=ws_id,
            name=command.name,
            agent_type=a_type,
        )

        async with self._uow:
            await self._agent_repo.save(agent)
            await self._uow.commit()

        return Result.ok(AgentMapper.to_dto(agent))
