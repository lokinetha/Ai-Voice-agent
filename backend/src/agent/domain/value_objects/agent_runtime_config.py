"""
AgentRuntimeConfig Value Object for Agent Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class AgentRuntimeConfig(ValueObject):
    """AgentRuntimeConfig Value Object storing execution runtime parameters."""

    max_concurrent_sessions: int = 10
    session_timeout_seconds: int = 600
    silence_threshold_ms: int = 800
    barge_in_enabled: bool = True

    def _validate(self) -> None:
        if self.max_concurrent_sessions < 1:
            raise ValueError("max_concurrent_sessions must be >= 1")
        if self.session_timeout_seconds < 10:
            raise ValueError("session_timeout_seconds must be >= 10")
        if self.silence_threshold_ms < 100:
            raise ValueError("silence_threshold_ms must be >= 100")

    @classmethod
    def default(cls) -> AgentRuntimeConfig:
        return cls(
            max_concurrent_sessions=10,
            session_timeout_seconds=600,
            silence_threshold_ms=800,
            barge_in_enabled=True,
        )
