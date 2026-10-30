"""
AgentType Value Object for Agent Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared.kernel.value_object import ValueObject


class AgentCategory(StrEnum):
    """Enumeration of Agent industry vertical types."""

    SALES = "SALES"
    SUPPORT = "SUPPORT"
    INSURANCE = "INSURANCE"
    HEALTHCARE = "HEALTHCARE"
    BANKING = "BANKING"
    LEGAL = "LEGAL"
    HR = "HR"
    BOOKING = "BOOKING"
    CUSTOM = "CUSTOM"


@dataclass(frozen=True)
class AgentType(ValueObject):
    """AgentType Value Object."""

    value: AgentCategory

    def _validate(self) -> None:
        if not isinstance(self.value, AgentCategory):
            if isinstance(self.value, str):
                try:
                    object.__setattr__(self, "value", AgentCategory(self.value.upper()))
                except ValueError as err:
                    raise ValueError(f"Invalid AgentType string: {self.value}") from err
            else:
                raise ValueError(f"AgentType value must be AgentCategory enum, got: {type(self.value)}")

    @classmethod
    def sales(cls) -> AgentType:
        return cls(value=AgentCategory.SALES)

    @classmethod
    def support(cls) -> AgentType:
        return cls(value=AgentCategory.SUPPORT)

    @classmethod
    def custom(cls) -> AgentType:
        return cls(value=AgentCategory.CUSTOM)
