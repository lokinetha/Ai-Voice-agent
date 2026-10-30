"""
KnowledgeBaseStatus Value Object for Knowledge Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared.kernel.value_object import ValueObject


class KBStatusType(StrEnum):
    """Enumeration of KnowledgeBase lifecycle status states."""

    ACTIVE = "ACTIVE"
    INDEXING = "INDEXING"
    DEGRADED = "DEGRADED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class KnowledgeBaseStatus(ValueObject):
    """KnowledgeBaseStatus Value Object."""

    value: KBStatusType

    def _validate(self) -> None:
        if not isinstance(self.value, KBStatusType):
            if isinstance(self.value, str):
                try:
                    object.__setattr__(self, "value", KBStatusType(self.value.upper()))
                except ValueError as err:
                    raise ValueError(f"Invalid KBStatus string: {self.value}") from err
            else:
                raise ValueError(f"KBStatus value must be KBStatusType enum, got: {type(self.value)}")

    @classmethod
    def active(cls) -> KnowledgeBaseStatus:
        return cls(value=KBStatusType.ACTIVE)

    @classmethod
    def indexing(cls) -> KnowledgeBaseStatus:
        return cls(value=KBStatusType.INDEXING)

    @classmethod
    def archived(cls) -> KnowledgeBaseStatus:
        return cls(value=KBStatusType.ARCHIVED)
