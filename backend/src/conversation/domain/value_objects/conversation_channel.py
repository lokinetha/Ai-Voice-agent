"""
ConversationChannel Value Object for Conversation Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared.kernel.value_object import ValueObject


class ChannelType(StrEnum):
    """Enumeration of Conversation communication channels."""

    VOICE = "VOICE"
    WEBCHAT = "WEBCHAT"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    API = "API"


@dataclass(frozen=True)
class ConversationChannel(ValueObject):
    """ConversationChannel Value Object."""

    value: ChannelType

    def _validate(self) -> None:
        if not isinstance(self.value, ChannelType):
            if isinstance(self.value, str):
                try:
                    object.__setattr__(self, "value", ChannelType(self.value.upper()))
                except ValueError as err:
                    raise ValueError(f"Invalid ConversationChannel string: {self.value}") from err
            else:
                raise ValueError(
                    f"ConversationChannel value must be ChannelType enum, got: {type(self.value)}"
                )

    @classmethod
    def voice(cls) -> ConversationChannel:
        return cls(value=ChannelType.VOICE)

    @classmethod
    def webchat(cls) -> ConversationChannel:
        return cls(value=ChannelType.WEBCHAT)

    @classmethod
    def api(cls) -> ConversationChannel:
        return cls(value=ChannelType.API)
