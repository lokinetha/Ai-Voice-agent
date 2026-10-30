"""
Pydantic Response Schemas for Conversation Presentation Layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ParticipantResponse(BaseModel):
    id: str
    name: str
    role: str
    external_id: str
    is_active: bool
    created_at: datetime


class MessageResponse(BaseModel):
    id: str
    participant_id: str
    participant_role: str
    content: str
    sequence_number: int
    metadata: dict[str, Any]
    created_at: datetime


class ConversationMetricsResponse(BaseModel):
    duration_seconds: float
    total_messages: int
    agent_messages: int
    customer_messages: int
    turn_count: int


class ConversationSummaryResponse(BaseModel):
    text: str
    key_topics: list[str]
    sentiment: str
    action_items: list[str]


class ConversationResponse(BaseModel):
    """HTTP Response schema representing a Conversation aggregate."""

    id: str = Field(..., description="Conversation ID")
    workspace_id: str = Field(..., description="Workspace ID")
    agent_id: str = Field(..., description="Agent ID")
    channel: str = Field(..., description="Communication channel")
    language: str = Field(..., description="Language code")
    status: str = Field(..., description="Status (ACTIVE, PAUSED, ENDED)")
    message_count: int = Field(..., description="Total messages")
    participant_count: int = Field(..., description="Total participants")
    version: int = Field(..., description="Optimistic concurrency version")
    created_at: datetime = Field(..., description="Creation timestamp")
    metrics: ConversationMetricsResponse | None = None
    summary: ConversationSummaryResponse | None = None
    participants: list[ParticipantResponse] = Field(default_factory=list)
    messages: list[MessageResponse] = Field(default_factory=list)
