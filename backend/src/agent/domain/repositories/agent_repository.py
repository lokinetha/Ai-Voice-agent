"""
AgentRepository Domain Interface for Agent Bounded Context.

Extends generic Repository interface for Agent aggregate root persistence operations.
"""

from __future__ import annotations

from abc import abstractmethod

from shared.kernel.repository import Repository
from shared.kernel.value_objects import AgentId, WorkspaceId

from agent.domain.entities.agent import Agent


class AgentRepository(Repository[Agent, AgentId]):
    """Domain Repository Interface for Agent Aggregate Root."""

    @abstractmethod
    async def get_by_workspace_and_name(
        self, workspace_id: WorkspaceId, name: str
    ) -> Agent | None:
        """Find Agent by workspace ID and name string.

        Used to enforce aggregate invariant: Agent name must be unique within a Workspace.

        Args:
            workspace_id: WorkspaceId value object.
            name: Agent name string.

        Returns:
            Agent aggregate root if found, or None.
        """
        ...

    @abstractmethod
    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[Agent]:
        """Find all Agents belonging to target WorkspaceId.

        Args:
            workspace_id: WorkspaceId value object.

        Returns:
            List of matching Agent aggregate roots.
        """
        ...
