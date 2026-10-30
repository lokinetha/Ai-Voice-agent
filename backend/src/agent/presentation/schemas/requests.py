"""
Pydantic Request Schemas for Agent Presentation Layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateAgentRequest(BaseModel):
    """HTTP Request schema for creating a new Agent."""

    workspace_id: str = Field(..., description="Owning Workspace ID", examples=["ws-100"])
    name: str = Field(..., description="Agent name", examples=["Sales Outbound Bot"])
    agent_type: str = Field(default="SALES", description="Agent vertical category", examples=["SALES"])


class UpdateAgentRequest(BaseModel):
    """HTTP Request schema for updating Agent configurations."""

    name: str | None = Field(default=None, description="Updated name")
    playbook_id: str | None = Field(default=None, description="Associated Playbook ID")
    prompt_id: str | None = Field(default=None, description="Associated Prompt ID")
    tts_provider: str | None = Field(default=None, description="TTS provider (elevenlabs, deepgram)")
    voice_id: str | None = Field(default=None, description="TTS voice identifier")
    language: str | None = Field(default=None, description="Language code (en-US, es-ES)")
    llm_provider: str | None = Field(default=None, description="LLM provider (gemini, openai)")
    llm_model: str | None = Field(default=None, description="LLM model identifier")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Sampling temperature")


class CloneAgentRequest(BaseModel):
    """HTTP Request schema for cloning an existing Agent."""

    new_name: str = Field(..., description="Name for cloned agent", examples=["Sales Outbound Bot Copy"])
