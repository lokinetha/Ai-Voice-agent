"""
PlaybookRepository Domain Interface for Playbook Bounded Context.
"""

from __future__ import annotations

from abc import abstractmethod

from shared.kernel.repository import Repository
from shared.kernel.value_objects import PlaybookId, WorkspaceId

from playbook.domain.entities.playbook import Playbook


class PlaybookRepository(Repository[Playbook, PlaybookId]):
    """Domain Repository Interface for Playbook Aggregate Root."""

    @abstractmethod
    async def find_by_workspace(
        self, workspace_id: WorkspaceId
    ) -> list[Playbook]:
        """Find all Playbooks in target Workspace.

        Args:
            workspace_id: WorkspaceId value object.

        Returns:
            List of matching Playbook aggregate roots.
        """
        ...

    @abstractmethod
    async def find_published_version(
        self, playbook_id: PlaybookId, version_number: int
    ) -> Playbook | None:
        """Find a specific published version snapshot of a Playbook.

        Args:
            playbook_id: PlaybookId value object.
            version_number: Target version number.

        Returns:
            Matching Playbook snapshot or None.
        """
        ...
