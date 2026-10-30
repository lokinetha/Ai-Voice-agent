"""
ConversationAnalysisRepository Domain Interface for Processing Bounded Context.
"""

from __future__ import annotations

from abc import abstractmethod

from shared.kernel.repository import Repository
from shared.kernel.value_objects import (
    ConversationId,
    EntityId,
    WorkspaceId,
)

from processing.domain.entities.conversation_analysis import (
    ConversationAnalysis,
)


class ConversationAnalysisRepository(Repository[ConversationAnalysis, EntityId]):
    """Domain Repository Interface for ConversationAnalysis Aggregate Root."""

    @abstractmethod
    async def find_by_workspace(
        self, workspace_id: WorkspaceId
    ) -> list[ConversationAnalysis]:
        """Find all ConversationAnalysis records in target Workspace."""
        ...

    @abstractmethod
    async def find_by_conversation(
        self, conversation_id: ConversationId
    ) -> list[ConversationAnalysis]:
        """Find all ConversationAnalysis records for a target Conversation."""
        ...
