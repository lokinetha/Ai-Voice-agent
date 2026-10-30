"""
ConversationMetrics Value Object for Conversation Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class ConversationMetrics(ValueObject):
    """ConversationMetrics Value Object tracking conversation interaction counters."""

    duration_seconds: float = 0.0
    total_messages: int = 0
    agent_messages: int = 0
    customer_messages: int = 0
    turn_count: int = 0

    def _validate(self) -> None:
        if self.duration_seconds < 0.0:
            raise ValueError("duration_seconds cannot be negative")
        if self.total_messages < 0:
            raise ValueError("total_messages cannot be negative")
        if self.agent_messages < 0:
            raise ValueError("agent_messages cannot be negative")
        if self.customer_messages < 0:
            raise ValueError("customer_messages cannot be negative")
        if self.turn_count < 0:
            raise ValueError("turn_count cannot be negative")

    @classmethod
    def empty(cls) -> ConversationMetrics:
        return cls(
            duration_seconds=0.0,
            total_messages=0,
            agent_messages=0,
            customer_messages=0,
            turn_count=0,
        )
