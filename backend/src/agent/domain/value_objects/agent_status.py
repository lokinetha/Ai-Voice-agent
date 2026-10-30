"""
AgentStatus Value Object for Agent Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared.kernel.value_object import ValueObject


class AgentStatusType(StrEnum):
    """Enumeration of Agent lifecycle status states."""

    DRAFT = "DRAFT"
    TESTING = "TESTING"
    PUBLISHED = "PUBLISHED"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class AgentStatus(ValueObject):
    """AgentStatus Value Object."""

    value: AgentStatusType

    def _validate(self) -> None:
        if not isinstance(self.value, AgentStatusType):
            if isinstance(self.value, str):
                try:
                    object.__setattr__(self, "value", AgentStatusType(self.value.upper()))
                except ValueError as err:
                    raise ValueError(f"Invalid AgentStatus string: {self.value}") from err
            else:
                raise ValueError(f"AgentStatus value must be AgentStatusType enum, got: {type(self.value)}")

    @classmethod
    def draft(cls) -> AgentStatus:
        return cls(value=AgentStatusType.DRAFT)

    @classmethod
    def testing(cls) -> AgentStatus:
        return cls(value=AgentStatusType.TESTING)

    @classmethod
    def published(cls) -> AgentStatus:
        return cls(value=AgentStatusType.PUBLISHED)

    @classmethod
    def paused(cls) -> AgentStatus:
        return cls(value=AgentStatusType.PAUSED)

    @classmethod
    def archived(cls) -> AgentStatus:
        return cls(value=AgentStatusType.ARCHIVED)

    @property
    def is_published(self) -> bool:
        return self.value == AgentStatusType.PUBLISHED

    @property
    def is_archived(self) -> bool:
        return self.value == AgentStatusType.ARCHIVED
