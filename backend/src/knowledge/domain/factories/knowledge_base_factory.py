"""
KnowledgeBaseFactory for Knowledge Bounded Context.

Encapsulates construction of new KnowledgeBase Aggregate Roots.
"""

from __future__ import annotations

from shared.kernel.value_objects import KnowledgeBaseId, WorkspaceId

from knowledge.domain.entities.knowledge_base import KnowledgeBase
from knowledge.domain.events.knowledge_base_created import KnowledgeBaseCreated
from knowledge.domain.value_objects.kb_status import KnowledgeBaseStatus
from knowledge.domain.value_objects.retrieval_policy import RetrievalPolicy


class KnowledgeBaseFactory:
    """Factory constructing new KnowledgeBase Aggregate Roots."""

    @classmethod
    def create(
        self,
        workspace_id: WorkspaceId,
        name: str,
        description: str = "",
        retrieval_policy: RetrievalPolicy | None = None,
        kb_id: KnowledgeBaseId | None = None,
    ) -> KnowledgeBase:
        """Create and initialize a new KnowledgeBase aggregate root.

        Args:
            workspace_id: Owning WorkspaceId.
            name: KnowledgeBase name string.
            description: Optional description string.
            retrieval_policy: Optional custom RetrievalPolicy.
            kb_id: Optional explicit KnowledgeBaseId.

        Returns:
            Initialized KnowledgeBase aggregate with recorded KnowledgeBaseCreated event.
        """
        id_val = kb_id or KnowledgeBaseId()
        policy = retrieval_policy or RetrievalPolicy.default()

        kb = KnowledgeBase(
            id=id_val,
            workspace_id=workspace_id,
            name=name,
            description=description,
            status=KnowledgeBaseStatus.active(),
            retrieval_policy=policy,
            documents=(),
        )

        kb._raise_event(
            KnowledgeBaseCreated(
                kb_id=str(id_val.value),
                workspace_id=str(workspace_id.value),
                name=name,
            )
        )

        return kb
