"""
KnowledgeBaseIndexingService Domain Service for Knowledge Bounded Context.

Manages domain rules for reindexing and document chunk metadata validation.
Does NOT execute vector embedding calls or LLM model invocations.
"""

from __future__ import annotations

from shared.kernel.domain_service import DomainService
from shared.kernel.result import Error, Result

from knowledge.domain.entities.knowledge_base import KnowledgeBase
from knowledge.domain.specifications.active_knowledge_base_spec import (
    ActiveKnowledgeBaseSpec,
)


class KnowledgeBaseIndexingService(DomainService):
    """Domain Service managing KnowledgeBase reindexing logic."""

    def __init__(self) -> None:
        self._active_spec = ActiveKnowledgeBaseSpec()

    def validate_and_reindex(self, kb: KnowledgeBase) -> Result[None]:
        """Validate state and trigger KnowledgeBase reindexing event.

        Args:
            kb: KnowledgeBase aggregate root.

        Returns:
            Result indicating success or INVALID_STATE Error.
        """
        if not self._active_spec.is_satisfied_by(kb):
            return Result.fail(Error("INVALID_STATE", "Cannot reindex an archived or inactive KnowledgeBase"))

        return kb.reindex()
