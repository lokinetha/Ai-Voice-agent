"""
Pydantic Response Schemas for Prompt Presentation Layer.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PromptInstructionResponse(BaseModel):
    id: str
    text: str
    order: int
    is_mandatory: bool


class PromptSectionResponse(BaseModel):
    id: str
    section_type: str
    title: str
    content: str
    order: int
    instructions: list[PromptInstructionResponse] = Field(default_factory=list)


class PromptConstraintResponse(BaseModel):
    id: str
    constraint_type: str
    rule_text: str


class PromptExampleResponse(BaseModel):
    id: str
    user_input: str
    ideal_response: str
    context: str


class PromptCompilationMetadataResponse(BaseModel):
    source_playbook_id: str
    source_playbook_version: int
    compiled_at: datetime
    template_name: str
    checksum: str


class PromptVersionResponse(BaseModel):
    version_number: int
    label: str
    changelog: str


class PromptResponse(BaseModel):
    """HTTP Response schema representing a Prompt aggregate."""

    id: str = Field(..., description="Prompt ID")
    workspace_id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="Prompt title")
    description: str = Field(..., description="Prompt description")
    status: str = Field(..., description="Status (DRAFT, COMPILED, PUBLISHED, ARCHIVED)")
    compiled_prompt_text: str = Field(..., description="Final compiled system prompt text")
    version_info: PromptVersionResponse
    compilation_metadata: PromptCompilationMetadataResponse | None = None
    sections: list[PromptSectionResponse] = Field(default_factory=list)
    constraints: list[PromptConstraintResponse] = Field(default_factory=list)
    examples: list[PromptExampleResponse] = Field(default_factory=list)
    version: int = Field(..., description="Optimistic concurrency version")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
