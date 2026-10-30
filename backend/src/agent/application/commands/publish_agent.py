"""
PublishAgent Command and CommandHandler.
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
from agent.domain.services.agent_publishing_service import AgentPublishingService


@dataclass(frozen=True)
class PublishAgentCommand(Command):
    """Command requesting Agent publishing."""

    agent_id: str


class PublishAgentHandler(CommandHandler[PublishAgentCommand, AgentDTO]):
    """Handler executing PublishAgentCommand."""

    def __init__(
        self,
        agent_repository: AgentRepository,
        publishing_service: AgentPublishingService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._agent_repo = agent_repository
        self._publishing_service = publishing_service
        self._uow = unit_of_work

    async def handle(self, command: PublishAgentCommand) -> Result[AgentDTO]:
        """Execute Agent publishing while enforcing domain invariants (Playbook & Prompt presence).

        Args:
            command: PublishAgentCommand instance.

        Returns:
            Result wrapping published AgentDTO on success, or Error on failure.
        """
        agent = await self._agent_repo.get_by_id(AgentId(command.agent_id))
        if agent is None:
            return Result.fail(Error("NOT_FOUND", f"Agent '{command.agent_id}' not found"))

        # Domain Publishing Service validates invariants (Playbook ID, Prompt ID, status)
        publish_res = self._publishing_service.validate_and_publish(agent)
        if publish_res.is_failure:
            return Result.fail(publish_res.error)

        async with self._uow:
            await self._agent_repo.save(agent)
            await self._uow.commit()

        return Result.ok(AgentMapper.to_dto(agent))
