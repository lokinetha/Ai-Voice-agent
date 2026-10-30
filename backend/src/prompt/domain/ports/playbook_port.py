"""
Playbook Port Interface for Prompt Bounded Context.

Decouples the Prompt domain from the Playbook aggregate implementation.
Allows PromptCompilationService to consume structured Playbook data safely.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlaybookGoalData:
    name: str
    description: str
    priority: int
    is_mandatory: bool


@dataclass(frozen=True)
class PlaybookStageData:
    name: str
    order: int
    description: str
    goals: tuple[PlaybookGoalData, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PlaybookRuleData:
    name: str
    condition: str
    action: str
    is_strict: bool


@dataclass(frozen=True)
class PlaybookObjectionData:
    trigger_phrase: str
    objection_category: str
    response_strategy: str
    recommended_response: str


@dataclass(frozen=True)
class PlaybookExampleData:
    scenario: str
    user_input: str
    ideal_response: str
    explanation: str


@dataclass(frozen=True)
class PlaybookDataDTO:
    """Read-only DTO representing published Playbook data for Prompt compilation."""

    playbook_id: str
    version_number: int
    name: str
    description: str
    status: str  # Must be "PUBLISHED"
    persona_name: str
    persona_role: str
    persona_description: str
    tone: str
    formality: str
    pacing: str
    goals: tuple[PlaybookGoalData, ...] = field(default_factory=tuple)
    stages: tuple[PlaybookStageData, ...] = field(default_factory=tuple)
    rules: tuple[PlaybookRuleData, ...] = field(default_factory=tuple)
    objections: tuple[PlaybookObjectionData, ...] = field(default_factory=tuple)
    examples: tuple[PlaybookExampleData, ...] = field(default_factory=tuple)


class PlaybookQueryPort(ABC):
    """Abstract port for querying published Playbook data."""

    @abstractmethod
    async def get_published_playbook(
        self, playbook_id: str, version_number: int | None = None
    ) -> PlaybookDataDTO | None:
        """Fetch published Playbook data for compilation.

        Args:
            playbook_id: ID of Playbook.
            version_number: Optional version number (defaults to latest published).

        Returns:
            PlaybookDataDTO if found and published, else None.
        """
        ...
