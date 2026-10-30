"""
ActiveKnowledgeBaseSpec Specification for Knowledge Bounded Context.
"""

from __future__ import annotations

from shared.kernel.specification import Specification

from knowledge.domain.entities.knowledge_base import KnowledgeBase
from knowledge.domain.value_objects.kb_status import KBStatusType


class ActiveKnowledgeBaseSpec(Specification[KnowledgeBase]):
    """Specification matching active (non-archived) KnowledgeBases."""

    def is_satisfied_by(self, candidate: KnowledgeBase) -> bool:
        return candidate.status.value != KBStatusType.ARCHIVED
