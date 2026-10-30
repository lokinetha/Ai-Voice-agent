"""
ConversationStatus Value Object for Conversation Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared.kernel.value_object import ValueObject


class ConversationStatusType(StrEnum):
    """Enumeration of Conversation lifecycle states."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ENDED = "ENDED"


@dataclass(frozen=True)
class ConversationStatus(ValueObject):
    """ConversationStatus Value Object."""

    value: ConversationStatusType

    def _validate(self) -> None:
        if not isinstance(self.value, ConversationStatusType):
            if isinstance(self.value, str):
                try:
                    object.__setattr__(self, "value", ConversationStatusType(self.value.upper()))
                except ValueError as err:
                    raise ValueError(f"Invalid ConversationStatus string: {self.value}") from err
            else:
                raise ValueError(
                    f"ConversationStatus value must be ConversationStatusType enum, got: {type(self.value)}"
                )

    @classmethod
    def active(cls) -> ConversationStatus:
        return cls(value=ConversationStatusType.ACTIVE)

    @classmethod
    def paused(cls) -> ConversationStatus:
        return cls(value=ConversationStatusType.PAUSED)

    @classmethod
    def ended(cls) -> ConversationStatus:
        return cls(value=ConversationStatusType.ENDED)

    @property
    def is_active(self) -> bool:
        return self.value == ConversationStatusType.ACTIVE

    @property
    def is_paused(self) -> bool:
        return self.value == ConversationStatusType.PAUSED

    @property
    def is_ended(self) -> bool:
        return self.value == ConversationStatusType.ENDED
