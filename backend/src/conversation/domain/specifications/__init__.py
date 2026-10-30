"""
Conversation Domain Specifications package init.
"""

from conversation.domain.specifications.active_conversation_spec import (
    ActiveConversationSpec,
)
from conversation.domain.specifications.can_accept_message_spec import (
    CanAcceptMessageSpec,
)

__all__ = [
    "ActiveConversationSpec",
    "CanAcceptMessageSpec",
]
