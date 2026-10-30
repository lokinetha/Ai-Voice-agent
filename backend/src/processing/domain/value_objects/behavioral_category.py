"""
BehavioralCategory Value Object.

Categorizes behavioral signals and patterns extracted from conversation analysis.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


class CategoryType(enum.Enum):
    """Behavioral category enumeration."""

    OBJECTION_HANDLING = "OBJECTION_HANDLING"
    CLOSING_TECHNIQUE = "CLOSING_TECHNIQUE"
    DISCOVERY_QUESTION = "DISCOVERY_QUESTION"
    EMPATHY_BUILDING = "EMPATHY_BUILDING"
    COMPLIANCE_RULE = "COMPLIANCE_RULE"
    GENERAL = "GENERAL"


@dataclass(frozen=True)
class BehavioralCategory(ValueObject):
    """Immutable value object categorizing a behavioral signal or pattern."""

    category: CategoryType = CategoryType.GENERAL

    def _validate(self) -> None:
        if not isinstance(self.category, CategoryType):
            raise ValueError(f"Invalid CategoryType: {self.category}")

    @classmethod
    def objection_handling(cls) -> BehavioralCategory:
        return cls(CategoryType.OBJECTION_HANDLING)

    @classmethod
    def closing_technique(cls) -> BehavioralCategory:
        return cls(CategoryType.CLOSING_TECHNIQUE)

    @classmethod
    def discovery_question(cls) -> BehavioralCategory:
        return cls(CategoryType.DISCOVERY_QUESTION)

    @classmethod
    def empathy_building(cls) -> BehavioralCategory:
        return cls(CategoryType.EMPATHY_BUILDING)

    @classmethod
    def compliance_rule(cls) -> BehavioralCategory:
        return cls(CategoryType.COMPLIANCE_RULE)

    @classmethod
    def general(cls) -> BehavioralCategory:
        return cls(CategoryType.GENERAL)
