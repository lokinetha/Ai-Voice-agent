"""
Pydantic Response Schemas for Playbook Presentation Layer.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PersonaResponse(BaseModel):
    name: str
    role: str
    description: str
    industry: str


class CommunicationStyleResponse(BaseModel):
    tone: str
    formality: str
    pacing: str
    vocabulary_level: int
    use_filler_words: bool


class SuccessCriteriaResponse(BaseModel):
    primary_metric: str
    target_value: float
    secondary_metrics: list[str]
    description: str


class GoalResponse(BaseModel):
    id: str
    name: str
    description: str
    priority: int
    is_mandatory: bool


class StageResponse(BaseModel):
    id: str
    name: str
    order: int
    description: str
    goals: list[GoalResponse]


class RuleResponse(BaseModel):
    id: str
    name: str
    condition: str
    action: str
    is_strict: bool


class ObjectionResponse(BaseModel):
    id: str
    trigger_phrase: str
    objection_category: str
    response_strategy: str
    recommended_response: str


class ExampleResponse(BaseModel):
    id: str
    scenario: str
    user_input: str
    ideal_response: str
    explanation: str


class TransitionResponse(BaseModel):
    id: str
    from_stage_id: str
    to_stage_id: str
    condition: str


class PlaybookVersionResponse(BaseModel):
    version_number: int
    label: str
    changelog: str


class PlaybookResponse(BaseModel):
    """HTTP Response schema representing a Playbook aggregate."""

    id: str = Field(..., description="Playbook ID")
    workspace_id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="Playbook title")
    description: str = Field(..., description="Playbook description")
    status: str = Field(..., description="Status (DRAFT, PUBLISHED, ARCHIVED)")
    version_info: PlaybookVersionResponse
    persona: PersonaResponse | None = None
    communication_style: CommunicationStyleResponse | None = None
    success_criteria: SuccessCriteriaResponse | None = None
    goals: list[GoalResponse] = Field(default_factory=list)
    stages: list[StageResponse] = Field(default_factory=list)
    rules: list[RuleResponse] = Field(default_factory=list)
    objections: list[ObjectionResponse] = Field(default_factory=list)
    examples: list[ExampleResponse] = Field(default_factory=list)
    transitions: list[TransitionResponse] = Field(default_factory=list)
    version: int = Field(..., description="Optimistic concurrency version")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
