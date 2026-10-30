"""
Conversation Data Transfer Objects (DTOs) for Application Layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ParticipantDTO:
    """DTO representing a Conversation participant."""

    id: str
    name: str
    role: str
    external_id: str
    is_active: bool
    created_at: datetime


@dataclass(frozen=True)
class MessageDTO:
    """DTO representing a Conversation message."""

    id: str
    participant_id: str
    participant_role: str
    content: str
    sequence_number: int
    metadata: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True)
class ConversationSummaryDTO:
    """DTO representing a Conversation summary."""

    text: str
    key_topics: tuple[str, ...]
    sentiment: str
    action_items: tuple[str, ...]


@dataclass(frozen=True)
class ConversationMetricsDTO:
    """DTO representing Conversation metrics counters."""

    duration_seconds: float
    total_messages: int
    agent_messages: int
    customer_messages: int
    turn_count: int


@dataclass(frozen=True)
class ConversationDTO:
    """DTO representing a Conversation aggregate root."""

    id: str
    workspace_id: str
    agent_id: str
    channel: str
    language: str
    status: str
    message_count: int
    participant_count: int
    version: int
    created_at: datetime
    metrics: ConversationMetricsDTO | None = None
    summary: ConversationSummaryDTO | None = None
    participants: tuple[ParticipantDTO, ...] = field(default_factory=tuple)
    messages: tuple[MessageDTO, ...] = field(default_factory=tuple)
