"""
Provider-independent LLM Response DTO for Voice Infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMResponseDTO:
    """Provider-independent LLM response DTO returned by LLM adapters.

    Attributes:
        content: Generated plain text response string.
        model: Identifier of model used for generation.
        finish_reason: Termination reason (e.g., "STOP", "MAX_TOKENS", "SAFETY").
        prompt_tokens: Number of tokens in input prompt.
        candidate_tokens: Number of tokens in generated response candidate.
        total_tokens: Total tokens consumed (prompt + candidate).
        latency_ms: Execution duration in milliseconds.
        correlation_id: Correlation/session tracking identifier.
        metadata: Additional provider metadata dictionary.
    """

    content: str
    model: str = "gemini-2.5-flash"
    finish_reason: str = "STOP"
    prompt_tokens: int = 0
    candidate_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    correlation_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation returns plain text content for backwards compatibility."""
        return self.content
