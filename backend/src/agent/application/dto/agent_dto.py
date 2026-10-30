"""
Agent Data Transfer Objects (DTOs) for Application Layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class AgentVoiceConfigDTO:
    tts_provider: str
    voice_id: str
    speed: float
    pitch: float
    language: str


@dataclass(frozen=True)
class AgentRuntimeConfigDTO:
    max_concurrent_sessions: int
    session_timeout_seconds: int
    silence_threshold_ms: int
    barge_in_enabled: bool


@dataclass(frozen=True)
class AgentLLMConfigDTO:
    provider: str
    model: str
    temperature: float
    max_tokens: int
    context_window: int


@dataclass(frozen=True)
class AgentMemoryConfigDTO:
    short_term_window_size: int
    long_term_enabled: bool
    long_term_strategy: str


@dataclass(frozen=True)
class AgentToolDTO:
    id: str
    name: str
    tool_type: str
    schema: dict[str, Any]
    config: dict[str, Any]
    enabled: bool


@dataclass(frozen=True)
class AgentPolicyDTO:
    id: str
    policy_type: str
    rule: str
    violation_action: str
    enforced: bool
    priority: int


@dataclass(frozen=True)
class AgentDTO:
    """DTO representing Agent aggregate root."""

    id: str
    workspace_id: str
    name: str
    type: str
    status: str
    voice_config: AgentVoiceConfigDTO
    runtime_config: AgentRuntimeConfigDTO
    llm_config: AgentLLMConfigDTO
    memory_config: AgentMemoryConfigDTO
    playbook_id: str | None
    prompt_id: str | None
    tools: tuple[AgentToolDTO, ...]
    policies: tuple[AgentPolicyDTO, ...]
    version: int
    created_at: datetime
