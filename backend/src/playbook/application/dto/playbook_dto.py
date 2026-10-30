"""
Playbook Data Transfer Objects (DTOs) for Application Layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class PersonaDTO:
    """DTO representing an Agent Persona."""

    name: str
    role: str
    description: str
    industry: str


@dataclass(frozen=True)
class CommunicationStyleDTO:
    """DTO representing Agent Communication Style."""

    tone: str
    formality: str
    pacing: str
    vocabulary_level: int
    use_filler_words: bool


@dataclass(frozen=True)
class SuccessCriteriaDTO:
    """DTO representing Playbook Success Criteria."""

    primary_metric: str
    target_value: float
    secondary_metrics: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class GoalDTO:
    """DTO representing a Playbook Goal."""

    id: str
    name: str
    description: str
    priority: int
    is_mandatory: bool


@dataclass(frozen=True)
class StageDTO:
    """DTO representing a Playbook Stage."""

    id: str
    name: str
    order: int
    description: str
    goals: tuple[GoalDTO, ...]


@dataclass(frozen=True)
class RuleDTO:
    """DTO representing a Playbook Rule."""

    id: str
    name: str
    condition: str
    action: str
    is_strict: bool


@dataclass(frozen=True)
class ObjectionDTO:
    """DTO representing an Objection Handler."""

    id: str
    trigger_phrase: str
    objection_category: str
    response_strategy: str
    recommended_response: str


@dataclass(frozen=True)
class ExampleDTO:
    """DTO representing a Playbook Example."""

    id: str
    scenario: str
    user_input: str
    ideal_response: str
    explanation: str


@dataclass(frozen=True)
class TransitionDTO:
    """DTO representing a Stage Transition."""

    id: str
    from_stage_id: str
    to_stage_id: str
    condition: str


@dataclass(frozen=True)
class PlaybookVersionDTO:
    """DTO representing Playbook Version snapshot metadata."""

    version_number: int
    label: str
    changelog: str


@dataclass(frozen=True)
class PlaybookDTO:
    """DTO representing a Playbook aggregate root."""

    id: str
    workspace_id: str
    name: str
    description: str
    status: str
    version_info: PlaybookVersionDTO
    persona: PersonaDTO | None = None
    communication_style: CommunicationStyleDTO | None = None
    success_criteria: SuccessCriteriaDTO | None = None
    goals: tuple[GoalDTO, ...] = field(default_factory=tuple)
    stages: tuple[StageDTO, ...] = field(default_factory=tuple)
    rules: tuple[RuleDTO, ...] = field(default_factory=tuple)
    objections: tuple[ObjectionDTO, ...] = field(default_factory=tuple)
    examples: tuple[ExampleDTO, ...] = field(default_factory=tuple)
    transitions: tuple[TransitionDTO, ...] = field(default_factory=tuple)
    version: int = 1
    created_at: datetime | None = None
