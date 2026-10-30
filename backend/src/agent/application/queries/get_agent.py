"""
GetAgent Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import AgentId

from agent.application.dto.agent_dto import AgentDTO
from agent.application.mappers.agent_mapper import AgentMapper
from agent.domain.repositories.agent_repository import AgentRepository


@dataclass(frozen=True)
class GetAgentQuery(Query):
    """Query requesting Agent details by agent_id."""

    agent_id: str


class GetAgentHandler(QueryHandler[GetAgentQuery, AgentDTO]):
    """Handler executing GetAgentQuery."""

    def __init__(self, agent_repository: AgentRepository) -> None:
        self._agent_repo = agent_repository

    async def handle(self, query: GetAgentQuery) -> Result[AgentDTO]:
        """Execute GetAgentQuery."""
        if not query.agent_id:
            return Result.fail(Error("VALIDATION_ERROR", "Agent ID cannot be empty"))

        agent = await self._agent_repo.get_by_id(AgentId(query.agent_id))
        if agent is None:
            return Result.fail(Error("NOT_FOUND", f"Agent with ID '{query.agent_id}' not found"))

        return Result.ok(AgentMapper.to_dto(agent))
