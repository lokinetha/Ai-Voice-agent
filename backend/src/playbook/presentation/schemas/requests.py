"""
Pydantic Request Schemas for Playbook Presentation Layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreatePlaybookRequest(BaseModel):
    """HTTP Request schema for creating a Playbook."""

    workspace_id: str = Field(..., description="Owning Workspace ID")
    name: str = Field(..., description="Playbook title")
    description: str = Field(default="", description="Playbook description")
    persona_name: str = Field(default="", description="Persona display name")
    persona_role: str = Field(default="", description="Persona functional role")
    persona_description: str = Field(default="", description="Persona description")
    persona_industry: str = Field(default="", description="Persona target industry")
    tone: str = Field(default="PROFESSIONAL", description="Communication tone")
    formality: str = Field(default="SEMI_FORMAL", description="Formality level")
    pacing: str = Field(default="MODERATE", description="Response pacing")
    primary_metric: str = Field(default="", description="Primary success metric")
    target_value: float = Field(default=0.0, description="Target value for metric")


class UpdatePlaybookRequest(BaseModel):
    """HTTP Request schema for updating a Playbook."""

    name: str = Field(..., description="Playbook title")
    description: str = Field(default="", description="Playbook description")
    persona_name: str = Field(default="", description="Persona display name")
    persona_role: str = Field(default="", description="Persona functional role")
    persona_description: str = Field(default="", description="Persona description")
    persona_industry: str = Field(default="", description="Persona target industry")


class PublishPlaybookRequest(BaseModel):
    """HTTP Request schema for publishing a Playbook."""

    label: str = Field(default="", description="Human-readable version label (e.g., 'v1.0')")
    changelog: str = Field(default="", description="Release changelog summary")


class ArchivePlaybookRequest(BaseModel):
    """HTTP Request schema for archiving a Playbook."""

    reason: str = Field(default="", description="Reason for archiving")


class CreatePlaybookVersionRequest(BaseModel):
    """HTTP Request schema for creating an explicit Playbook version snapshot."""

    label: str = Field(default="", description="Version label")
    changelog: str = Field(default="", description="Changelog notes")
