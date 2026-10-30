"""
ConversationRepository Domain Interface for Conversation Bounded Context.
"""

from __future__ import annotations

from abc import abstractmethod

from shared.kernel.repository import Repository
from shared.kernel.value_objects import AgentId, ConversationId, WorkspaceId

from conversation.domain.entities.conversation import Conversation


class ConversationRepository(Repository[Conversation, ConversationId]):
    """Domain Repository Interface for Conversation Aggregate Root."""

    @abstractmethod
    async def find_by_workspace(
        self, workspace_id: WorkspaceId
    ) -> list[Conversation]:
        """Find all Conversations in target Workspace.

        Args:
            workspace_id: WorkspaceId value object.

        Returns:
            List of matching Conversation aggregate roots.
        """
        ...

    @abstractmethod
    async def find_by_agent(
        self, agent_id: AgentId
    ) -> list[Conversation]:
        """Find all Conversations handled by target Agent.

        Args:
            agent_id: AgentId value object.

        Returns:
            List of matching Conversation aggregate roots.
        """
        ...
