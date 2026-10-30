"""
ConversationSummary Value Object for Conversation Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class ConversationSummary(ValueObject):
    """ConversationSummary Value Object encapsulating post-conversation analytics."""

    text: str
    key_topics: tuple[str, ...] = field(default_factory=tuple)
    sentiment: str = "neutral"
    action_items: tuple[str, ...] = field(default_factory=tuple)

    def _validate(self) -> None:
        if not isinstance(self.text, str):
            raise ValueError("text must be a string")
        if self.sentiment not in ("positive", "negative", "neutral", "mixed"):
            raise ValueError(f"Invalid sentiment string: {self.sentiment}")

    @classmethod
    def empty(cls) -> ConversationSummary:
        return cls(text="", key_topics=(), sentiment="neutral", action_items=())
