"""
AgentConfigReaderPort Interface for Agent Runtime.

Abstract port for loading active Agent configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agent_runtime.application.dto.agent_runtime_dto import AgentConfigDTO


class AgentConfigReaderPort(ABC):
    """Abstract port reading active Agent configuration."""

    @abstractmethod
    async def get_agent_config(
        self, workspace_id: str, agent_id: str
    ) -> AgentConfigDTO | None:
        """Load Agent configuration for given workspace and agent ID.

        Args:
            workspace_id: Owning Workspace ID.
            agent_id: Target Agent ID.

        Returns:
            AgentConfigDTO if found and active, else None.
        """
        ...
