"""
Pydantic Request Schemas for Prompt Presentation Layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreatePromptRequest(BaseModel):
    """HTTP Request schema for creating a Prompt."""

    workspace_id: str = Field(..., description="Owning Workspace ID")
    name: str = Field(..., description="Prompt title")
    description: str = Field(default="", description="Prompt description")


class CompilePromptRequest(BaseModel):
    """HTTP Request schema for compiling a Prompt from a published Playbook."""

    playbook_id: str = Field(..., description="ID of source published Playbook")
    playbook_version: int | None = Field(
        default=None, description="Optional version number (defaults to latest published)"
    )


class UpdatePromptRequest(BaseModel):
    """HTTP Request schema for updating Prompt metadata."""

    name: str = Field(..., description="Prompt title")
    description: str = Field(default="", description="Prompt description")


class PublishPromptRequest(BaseModel):
    """HTTP Request schema for publishing a Prompt."""

    label: str = Field(default="", description="Human-readable version label (e.g., 'v1.0')")
    changelog: str = Field(default="", description="Release changelog notes")


class ArchivePromptRequest(BaseModel):
    """HTTP Request schema for archiving a Prompt."""

    reason: str = Field(default="", description="Reason for archiving")


class CreatePromptVersionRequest(BaseModel):
    """HTTP Request schema for creating an explicit Prompt version snapshot."""

    label: str = Field(default="", description="Version label")
    changelog: str = Field(default="", description="Changelog notes")
