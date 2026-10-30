"""
AgentLLMConfig Value Object for Agent Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class AgentLLMConfig(ValueObject):
    """AgentLLMConfig Value Object storing inference model parameters."""

    provider: str = "gemini"
    model: str = "gemini-2.0-flash"
    temperature: float = 0.2
    max_tokens: int = 500
    context_window: int = 128000

    def _validate(self) -> None:
        if not self.provider or not isinstance(self.provider, str):
            raise ValueError("provider cannot be empty")
        if not self.model or not isinstance(self.model, str):
            raise ValueError("model cannot be empty")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"temperature must be between 0.0 and 2.0, got: {self.temperature}")
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")
        if self.context_window < 512:
            raise ValueError("context_window must be >= 512")

    @classmethod
    def default(cls) -> AgentLLMConfig:
        return cls(
            provider="gemini",
            model="gemini-2.0-flash",
            temperature=0.2,
            max_tokens=500,
            context_window=128000,
        )
