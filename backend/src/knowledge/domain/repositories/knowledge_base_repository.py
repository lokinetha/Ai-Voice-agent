"""
KnowledgeBaseRepository Domain Interface for Knowledge Bounded Context.

Extends generic Repository interface for KnowledgeBase aggregate root persistence operations.
"""

from __future__ import annotations

from abc import abstractmethod

from shared.kernel.repository import Repository
from shared.kernel.value_objects import KnowledgeBaseId, WorkspaceId

from knowledge.domain.entities.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository(Repository[KnowledgeBase, KnowledgeBaseId]):
    """Domain Repository Interface for KnowledgeBase Aggregate Root."""

    @abstractmethod
    async def get_by_workspace_and_name(
        self, workspace_id: WorkspaceId, name: str
    ) -> KnowledgeBase | None:
        """Find KnowledgeBase by workspace ID and name string.

        Args:
            workspace_id: WorkspaceId value object.
            name: KnowledgeBase name string.

        Returns:
            KnowledgeBase aggregate root if found, or None.
        """
        ...

    @abstractmethod
    async def find_by_workspace(
        self, workspace_id: WorkspaceId
    ) -> list[KnowledgeBase]:
        """Find all KnowledgeBases belonging to target WorkspaceId.

        Args:
            workspace_id: WorkspaceId value object.

        Returns:
            List of matching KnowledgeBase aggregate roots.
        """
        ...
