"""
ConversationLifecycleService Domain Service for Conversation Bounded Context.

Orchestrates conversation lifecycle state transitions using domain specifications.
"""

from __future__ import annotations

from shared.kernel.domain_service import DomainService
from shared.kernel.result import Error, Result

from conversation.domain.entities.conversation import Conversation
from conversation.domain.specifications.can_accept_message_spec import (
    CanAcceptMessageSpec,
)


class ConversationLifecycleService(DomainService):
    """Domain Service managing Conversation lifecycle transitions."""

    def __init__(self) -> None:
        self._can_accept_spec = CanAcceptMessageSpec()

    def end_conversation(self, conv: Conversation, reason: str = "") -> Result[None]:
        """Validate state and end a Conversation.

        Args:
            conv: Conversation aggregate root.
            reason: Human-readable reason for ending.

        Returns:
            Result indicating success or INVALID_STATE Error.
        """
        if conv.status.is_ended:
            return Result.fail(Error("INVALID_STATE", "Conversation is already ended"))

        return conv.end(reason)

    def can_accept_message(self, conv: Conversation) -> bool:
        """Check whether a Conversation can accept new messages.

        Args:
            conv: Conversation aggregate root.

        Returns:
            True if messages can be added.
        """
        return self._can_accept_spec.is_satisfied_by(conv)
