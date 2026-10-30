"""
ListAgents Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import WorkspaceId

from agent.application.dto.agent_dto import AgentDTO
from agent.application.mappers.agent_mapper import AgentMapper
from agent.domain.repositories.agent_repository import AgentRepository


@dataclass(frozen=True)
class ListAgentsQuery(Query):
    """Query requesting Agents list for a target workspace_id."""

    workspace_id: str


class ListAgentsHandler(QueryHandler[ListAgentsQuery, tuple[AgentDTO, ...]]):
    """Handler executing ListAgentsQuery."""

    def __init__(self, agent_repository: AgentRepository) -> None:
        self._agent_repo = agent_repository

    async def handle(self, query: ListAgentsQuery) -> Result[tuple[AgentDTO, ...]]:
        """Execute ListAgentsQuery."""
        if not query.workspace_id:
            return Result.fail(Error("VALIDATION_ERROR", "Workspace ID cannot be empty"))

        agents = await self._agent_repo.find_by_workspace(WorkspaceId(query.workspace_id))
        dtos = tuple(AgentMapper.to_dto(a) for a in agents)
        return Result.ok(dtos)
