"""
ParticipantRole Value Object for Conversation Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared.kernel.value_object import ValueObject


class RoleCategory(StrEnum):
    """Enumeration of Participant roles in a Conversation."""

    AGENT = "AGENT"
    CUSTOMER = "CUSTOMER"
    SUPERVISOR = "SUPERVISOR"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class ParticipantRole(ValueObject):
    """ParticipantRole Value Object."""

    value: RoleCategory

    def _validate(self) -> None:
        if not isinstance(self.value, RoleCategory):
            if isinstance(self.value, str):
                try:
                    object.__setattr__(self, "value", RoleCategory(self.value.upper()))
                except ValueError as err:
                    raise ValueError(f"Invalid ParticipantRole string: {self.value}") from err
            else:
                raise ValueError(
                    f"ParticipantRole value must be RoleCategory enum, got: {type(self.value)}"
                )

    @classmethod
    def agent(cls) -> ParticipantRole:
        return cls(value=RoleCategory.AGENT)

    @classmethod
    def customer(cls) -> ParticipantRole:
        return cls(value=RoleCategory.CUSTOMER)

    @classmethod
    def supervisor(cls) -> ParticipantRole:
        return cls(value=RoleCategory.SUPERVISOR)

    @classmethod
    def system(cls) -> ParticipantRole:
        return cls(value=RoleCategory.SYSTEM)

    @property
    def is_agent(self) -> bool:
        return self.value == RoleCategory.AGENT

    @property
    def is_customer(self) -> bool:
        return self.value == RoleCategory.CUSTOMER
