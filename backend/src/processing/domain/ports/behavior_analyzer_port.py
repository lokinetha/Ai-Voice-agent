"""
BehaviorAnalyzerPort Interface for Processing Bounded Context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from processing.domain.entities.behavioral_signal import BehavioralSignal
from processing.domain.entities.conversation_pattern import ConversationPattern


class BehaviorAnalyzerPort(ABC):
    """Abstract port for extracting behavioral signals and patterns from messages."""

    @abstractmethod
    async def analyze_messages(
        self, messages: list[dict[str, Any]], conversation_id: str = ""
    ) -> tuple[list[BehavioralSignal], list[ConversationPattern]]:
        """Analyze message turns and return detected signals and aggregated patterns.

        Args:
            messages: List of message dictionaries.
            conversation_id: ID of the conversation.

        Returns:
            Tuple of (detected_signals, detected_patterns).
        """
        ...
