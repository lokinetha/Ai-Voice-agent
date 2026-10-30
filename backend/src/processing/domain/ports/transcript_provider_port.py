"""
TranscriptProviderPort Interface for Processing Bounded Context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TranscriptProviderPort(ABC):
    """Abstract port for providing structured message transcripts for analysis."""

    @abstractmethod
    async def get_transcript_messages(
        self, conversation_id: str
    ) -> list[dict[str, Any]]:
        """Fetch structured transcript turns for analysis.

        Args:
            conversation_id: Target Conversation ID.

        Returns:
            List of message dictionaries containing "id", "role", "content", "sequence_number".
        """
        ...
