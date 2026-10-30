"""
Data Transfer Objects for Agent Runtime Application Orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentConfigDTO:
    """DTO representing runtime configuration for an Agent."""

    agent_id: str
    workspace_id: str
    name: str
    is_active: bool = True
    model_name: str = "gemini-2.5-flash"
    temperature: float = 0.7
    max_output_tokens: int = 1024
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PublishedPromptDTO:
    """DTO representing a compiled, published Prompt version for an Agent."""

    prompt_id: str
    agent_id: str
    workspace_id: str
    version: int
    compiled_template: str
    is_published: bool = True


@dataclass(frozen=True)
class ConversationTurnDTO:
    """DTO representing a single conversation history message turn."""

    message_id: str
    role: str
    content: str


@dataclass(frozen=True)
class AgentResponse:
    """Provider-independent response returned by AgentRuntimeService."""

    content: str
    agent_id: str
    conversation_id: str
    workspace_id: str
    correlation_id: str
    model_name: str = "gemini-2.5-flash"
    finish_reason: str = "STOP"
    prompt_tokens: int = 0
    candidate_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
