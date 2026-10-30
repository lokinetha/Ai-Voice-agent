"""
PromptStatus Value Object.

Represents the lifecycle status of a Prompt aggregate.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


class PromptStatusType(enum.Enum):
    """Prompt lifecycle status enumeration."""

    DRAFT = "DRAFT"
    COMPILED = "COMPILED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class PromptStatus(ValueObject):
    """Immutable value object representing Prompt lifecycle status."""

    value: PromptStatusType = PromptStatusType.DRAFT

    def _validate(self) -> None:
        if not isinstance(self.value, PromptStatusType):
            raise ValueError(f"Invalid PromptStatus: {self.value}")

    @property
    def is_draft(self) -> bool:
        return self.value == PromptStatusType.DRAFT

    @property
    def is_compiled(self) -> bool:
        return self.value == PromptStatusType.COMPILED

    @property
    def is_published(self) -> bool:
        return self.value == PromptStatusType.PUBLISHED

    @property
    def is_archived(self) -> bool:
        return self.value == PromptStatusType.ARCHIVED

    @classmethod
    def draft(cls) -> PromptStatus:
        return cls(PromptStatusType.DRAFT)

    @classmethod
    def compiled(cls) -> PromptStatus:
        return cls(PromptStatusType.COMPILED)

    @classmethod
    def published(cls) -> PromptStatus:
        return cls(PromptStatusType.PUBLISHED)

    @classmethod
    def archived(cls) -> PromptStatus:
        return cls(PromptStatusType.ARCHIVED)
