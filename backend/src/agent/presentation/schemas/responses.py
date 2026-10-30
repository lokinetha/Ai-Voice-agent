"""
Pydantic Response Schemas for Agent Presentation Layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentVoiceConfigResponse(BaseModel):
    tts_provider: str
    voice_id: str
    speed: float
    pitch: float
    language: str


class AgentRuntimeConfigResponse(BaseModel):
    max_concurrent_sessions: int
    session_timeout_seconds: int
    silence_threshold_ms: int
    barge_in_enabled: bool


class AgentLLMConfigResponse(BaseModel):
    provider: str
    model: str
    temperature: float
    max_tokens: int
    context_window: int


class AgentMemoryConfigResponse(BaseModel):
    short_term_window_size: int
    long_term_enabled: bool
    long_term_strategy: str


class AgentToolResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    tool_type: str
    tool_schema: dict[str, Any] = Field(..., alias="schema")
    tool_config: dict[str, Any] = Field(..., alias="config")
    enabled: bool


class AgentPolicyResponse(BaseModel):
    id: str
    policy_type: str
    rule: str
    violation_action: str
    enforced: bool
    priority: int


class AgentResponse(BaseModel):
    """HTTP Response schema representing an Agent aggregate."""

    id: str = Field(..., description="Agent ID")
    workspace_id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="Agent name")
    type: str = Field(..., description="Agent type/category")
    status: str = Field(..., description="Lifecycle status (DRAFT, PUBLISHED, etc.)")
    voice_config: AgentVoiceConfigResponse
    runtime_config: AgentRuntimeConfigResponse
    llm_config: AgentLLMConfigResponse
    memory_config: AgentMemoryConfigResponse
    playbook_id: str | None = Field(default=None, description="Associated Playbook ID")
    prompt_id: str | None = Field(default=None, description="Associated Prompt ID")
    tools: list[AgentToolResponse]
    policies: list[AgentPolicyResponse]
    version: int = Field(..., description="Optimistic concurrency version")
    created_at: datetime = Field(..., description="Creation timestamp")
