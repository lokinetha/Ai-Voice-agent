"""
AgentMemoryConfig Value Object for Agent Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class AgentMemoryConfig(ValueObject):
    """AgentMemoryConfig Value Object storing conversation memory settings."""

    short_term_window_size: int = 10
    long_term_enabled: bool = True
    long_term_strategy: str = "vector_search"

    def _validate(self) -> None:
        if self.short_term_window_size < 1:
            raise ValueError("short_term_window_size must be >= 1")
        if not self.long_term_strategy or not isinstance(self.long_term_strategy, str):
            raise ValueError("long_term_strategy cannot be empty")

    @classmethod
    def default(cls) -> AgentMemoryConfig:
        return cls(
            short_term_window_size=10,
            long_term_enabled=True,
            long_term_strategy="vector_search",
        )
