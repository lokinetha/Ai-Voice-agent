"""
Pydantic Request Schemas for Conversation Presentation Layer.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StartConversationRequest(BaseModel):
    """HTTP Request schema for starting a new Conversation."""

    workspace_id: str = Field(..., description="Owning Workspace ID")
    agent_id: str = Field(..., description="Agent ID handling the conversation")
    channel: str = Field(..., description="Channel (VOICE, WEBCHAT, SMS, WHATSAPP, API)")
    participant_name: str = Field(..., description="Customer participant name")
    customer_external_id: str = Field(default="", description="External customer identifier")
    language: str = Field(default="en-US", description="BCP 47 language code")


class AddMessageRequest(BaseModel):
    """HTTP Request schema for adding a message to a Conversation."""

    participant_id: str = Field(..., description="Participant ID sending the message")
    role: str = Field(..., description="Participant role (AGENT, CUSTOMER, SUPERVISOR, SYSTEM)")
    content: str = Field(..., description="Message content text")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata")


class PauseConversationRequest(BaseModel):
    """HTTP Request schema for pausing a Conversation."""

    reason: str = Field(default="", description="Reason for pausing")


class EndConversationRequest(BaseModel):
    """HTTP Request schema for ending a Conversation."""

    reason: str = Field(default="", description="Reason for ending")


class SummarizeConversationRequest(BaseModel):
    """HTTP Request schema for attaching a summary to a Conversation."""

    summary_text: str = Field(..., description="Summary text")
    key_topics: list[str] = Field(default_factory=list, description="Key discussion topics")
    sentiment: str = Field(default="neutral", description="Overall sentiment")
    action_items: list[str] = Field(default_factory=list, description="Follow-up action items")


class SearchConversationRequest(BaseModel):
    """HTTP Request schema for searching Conversations."""

    agent_id: str | None = Field(default=None, description="Filter by Agent ID")
    status: str | None = Field(default=None, description="Filter by status")
