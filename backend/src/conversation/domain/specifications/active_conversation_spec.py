"""
ActiveConversationSpec Specification for Conversation Bounded Context.
"""

from __future__ import annotations

from shared.kernel.specification import Specification

from conversation.domain.entities.conversation import Conversation


class ActiveConversationSpec(Specification[Conversation]):
    """Specification matching active (non-ended) Conversations."""

    def is_satisfied_by(self, candidate: Conversation) -> bool:
        return candidate.status.is_active
