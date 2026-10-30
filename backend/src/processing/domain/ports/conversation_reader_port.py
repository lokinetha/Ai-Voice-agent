"""
ConversationReaderPort Interface for Processing Bounded Context.

Abstract port for fetching completed conversation data without depending on
Conversation aggregate details.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConversationMessageData:
    """Read-only message representation for analysis."""

    id: str
    participant_id: str
    role: str
    content: str
    sequence_number: int


@dataclass(frozen=True)
class ConversationAnalysisDataDTO:
    """Read-only conversation representation for behavioral analysis."""

    conversation_id: str
    workspace_id: str
    agent_id: str
    status: str
    messages: tuple[ConversationMessageData, ...] = field(default_factory=tuple)


class ConversationReaderPort(ABC):
    """Abstract port for reading completed conversation content."""

    @abstractmethod
    async def get_completed_conversation(
        self, conversation_id: str
    ) -> ConversationAnalysisDataDTO | None:
        """Fetch completed conversation data.

        Args:
            conversation_id: ID of target Conversation.

        Returns:
            ConversationAnalysisDataDTO if found, else None.
        """
        ...
