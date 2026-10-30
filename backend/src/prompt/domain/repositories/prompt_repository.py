"""
PromptRepository Domain Interface for Prompt Bounded Context.
"""

from __future__ import annotations

from abc import abstractmethod

from shared.kernel.repository import Repository
from shared.kernel.value_objects import PromptId, WorkspaceId

from prompt.domain.entities.prompt import Prompt


class PromptRepository(Repository[Prompt, PromptId]):
    """Domain Repository Interface for Prompt Aggregate Root."""

    @abstractmethod
    async def find_by_workspace(
        self, workspace_id: WorkspaceId
    ) -> list[Prompt]:
        """Find all Prompts in target Workspace.

        Args:
            workspace_id: WorkspaceId value object.

        Returns:
            List of matching Prompt aggregate roots.
        """
        ...

    @abstractmethod
    async def find_published_version(
        self, prompt_id: PromptId, version_number: int
    ) -> Prompt | None:
        """Find a specific published version snapshot of a Prompt.

        Args:
            prompt_id: PromptId value object.
            version_number: Target version number.

        Returns:
            Matching Prompt snapshot or None.
        """
        ...
