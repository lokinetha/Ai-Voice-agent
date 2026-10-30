"""
PublishedPromptReaderPort Interface for Agent Runtime.

Abstract port for loading compiled, published Prompt versions.
Rule: Only published Prompt versions may be used by the runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agent_runtime.application.dto.agent_runtime_dto import PublishedPromptDTO


class PublishedPromptReaderPort(ABC):
    """Abstract port reading published Prompt versions."""

    @abstractmethod
    async def get_published_prompt(
        self, workspace_id: str, agent_id: str
    ) -> PublishedPromptDTO | None:
        """Load active published Prompt version for given agent.

        Args:
            workspace_id: Owning Workspace ID.
            agent_id: Target Agent ID.

        Returns:
            PublishedPromptDTO if a published version exists, else None.
        """
        ...
