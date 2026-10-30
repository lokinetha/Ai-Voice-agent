"""
Prompt Data Transfer Objects (DTOs) for Application Layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class PromptInstructionDTO:
    """DTO representing a Prompt Instruction line."""

    id: str
    text: str
    order: int
    is_mandatory: bool


@dataclass(frozen=True)
class PromptSectionDTO:
    """DTO representing a Prompt Section."""

    id: str
    section_type: str
    title: str
    content: str
    order: int
    instructions: tuple[PromptInstructionDTO, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PromptConstraintDTO:
    """DTO representing a Prompt Constraint."""

    id: str
    constraint_type: str
    rule_text: str


@dataclass(frozen=True)
class PromptExampleDTO:
    """DTO representing a Prompt Example."""

    id: str
    user_input: str
    ideal_response: str
    context: str


@dataclass(frozen=True)
class PromptCompilationMetadataDTO:
    """DTO representing Prompt compilation provenance metadata."""

    source_playbook_id: str
    source_playbook_version: int
    compiled_at: datetime
    template_name: str
    checksum: str


@dataclass(frozen=True)
class PromptVersionDTO:
    """DTO representing published Prompt version snapshot metadata."""

    version_number: int
    label: str
    changelog: str


@dataclass(frozen=True)
class PromptDTO:
    """DTO representing a Prompt aggregate root."""

    id: str
    workspace_id: str
    name: str
    description: str
    status: str
    compiled_prompt_text: str
    version_info: PromptVersionDTO
    compilation_metadata: PromptCompilationMetadataDTO | None = None
    sections: tuple[PromptSectionDTO, ...] = field(default_factory=tuple)
    constraints: tuple[PromptConstraintDTO, ...] = field(default_factory=tuple)
    examples: tuple[PromptExampleDTO, ...] = field(default_factory=tuple)
    version: int = 1
    created_at: datetime | None = None
