"""
PlaybookStatus Value Object.

Represents the lifecycle status of a Playbook aggregate.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


class PlaybookStatusType(enum.Enum):
    """Playbook lifecycle status enumeration."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class PlaybookStatus(ValueObject):
    """Immutable value object representing Playbook lifecycle status."""

    value: PlaybookStatusType = PlaybookStatusType.DRAFT

    def _validate(self) -> None:
        if not isinstance(self.value, PlaybookStatusType):
            raise ValueError(f"Invalid PlaybookStatus: {self.value}")

    @property
    def is_draft(self) -> bool:
        return self.value == PlaybookStatusType.DRAFT

    @property
    def is_published(self) -> bool:
        return self.value == PlaybookStatusType.PUBLISHED

    @property
    def is_archived(self) -> bool:
        return self.value == PlaybookStatusType.ARCHIVED

    @classmethod
    def draft(cls) -> PlaybookStatus:
        return cls(PlaybookStatusType.DRAFT)

    @classmethod
    def published(cls) -> PlaybookStatus:
        return cls(PlaybookStatusType.PUBLISHED)

    @classmethod
    def archived(cls) -> PlaybookStatus:
        return cls(PlaybookStatusType.ARCHIVED)
