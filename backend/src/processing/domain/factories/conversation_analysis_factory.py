"""
ConversationAnalysisFactory for Processing Bounded Context.
"""

from __future__ import annotations

from shared.kernel.value_objects import (
    ConversationId,
    EntityId,
    WorkspaceId,
)

from processing.domain.entities.conversation_analysis import (
    ConversationAnalysis,
)


class ConversationAnalysisFactory:
    """Factory constructing new ConversationAnalysis Aggregate Roots."""

    @classmethod
    def create(
        cls,
        workspace_id: WorkspaceId,
        conversation_id: ConversationId,
        analysis_id: EntityId | None = None,
    ) -> ConversationAnalysis:
        """Create a new ConversationAnalysis aggregate root.

        Args:
            workspace_id: Owning WorkspaceId.
            conversation_id: Target ConversationId.
            analysis_id: Optional explicit EntityId.

        Returns:
            Initialized ConversationAnalysis aggregate root.
        """
        id_val = analysis_id or EntityId()

        return ConversationAnalysis(
            id=id_val,
            workspace_id=workspace_id,
            conversation_id=conversation_id,
        )
