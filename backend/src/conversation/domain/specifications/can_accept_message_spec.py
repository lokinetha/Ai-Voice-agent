"""
CanAcceptMessageSpec Specification for Conversation Bounded Context.
"""

from __future__ import annotations

from shared.kernel.specification import Specification

from conversation.domain.entities.conversation import Conversation


class CanAcceptMessageSpec(Specification[Conversation]):
    """Specification checking whether a Conversation can accept new messages."""

    def is_satisfied_by(self, candidate: Conversation) -> bool:
        return not candidate.status.is_ended
