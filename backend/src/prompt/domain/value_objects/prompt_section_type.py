"""
PromptSectionType Value Object.

Categorizes sections within a compiled Prompt.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


class SectionCategory(enum.Enum):
    """Section category enumeration."""

    PERSONA = "PERSONA"
    GOALS = "GOALS"
    RULES = "RULES"
    STAGES = "STAGES"
    OBJECTIONS = "OBJECTIONS"
    EXAMPLES = "EXAMPLES"
    CONSTRAINTS = "CONSTRAINTS"
    GENERAL = "GENERAL"


@dataclass(frozen=True)
class PromptSectionType(ValueObject):
    """Immutable value object categorizing a Prompt section."""

    category: SectionCategory = SectionCategory.GENERAL

    def _validate(self) -> None:
        if not isinstance(self.category, SectionCategory):
            raise ValueError(f"Invalid SectionCategory: {self.category}")

    @classmethod
    def persona(cls) -> PromptSectionType:
        return cls(SectionCategory.PERSONA)

    @classmethod
    def goals(cls) -> PromptSectionType:
        return cls(SectionCategory.GOALS)

    @classmethod
    def rules(cls) -> PromptSectionType:
        return cls(SectionCategory.RULES)

    @classmethod
    def stages(cls) -> PromptSectionType:
        return cls(SectionCategory.STAGES)

    @classmethod
    def objections(cls) -> PromptSectionType:
        return cls(SectionCategory.OBJECTIONS)

    @classmethod
    def examples(cls) -> PromptSectionType:
        return cls(SectionCategory.EXAMPLES)

    @classmethod
    def constraints(cls) -> PromptSectionType:
        return cls(SectionCategory.CONSTRAINTS)

    @classmethod
    def general(cls) -> PromptSectionType:
        return cls(SectionCategory.GENERAL)
