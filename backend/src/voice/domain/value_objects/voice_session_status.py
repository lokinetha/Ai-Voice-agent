"""
VoiceSessionStatus Value Object.

Represents the state of a VoiceSession aggregate root.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


class VoiceSessionStatusType(enum.Enum):
    """Voice session status enumeration."""

    IDLE = "IDLE"
    CONNECTING = "CONNECTING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ENDED = "ENDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class VoiceSessionStatus(ValueObject):
    """Immutable value object for voice session status."""

    value: VoiceSessionStatusType = VoiceSessionStatusType.IDLE

    def _validate(self) -> None:
        if not isinstance(self.value, VoiceSessionStatusType):
            raise ValueError(f"Invalid VoiceSessionStatus: {self.value}")

    @property
    def is_idle(self) -> bool:
        return self.value == VoiceSessionStatusType.IDLE

    @property
    def is_active(self) -> bool:
        return self.value == VoiceSessionStatusType.ACTIVE

    @property
    def is_paused(self) -> bool:
        return self.value == VoiceSessionStatusType.PAUSED

    @property
    def is_ended(self) -> bool:
        return self.value == VoiceSessionStatusType.ENDED

    @property
    def is_failed(self) -> bool:
        return self.value == VoiceSessionStatusType.FAILED

    @classmethod
    def idle(cls) -> VoiceSessionStatus:
        return cls(VoiceSessionStatusType.IDLE)

    @classmethod
    def connecting(cls) -> VoiceSessionStatus:
        return cls(VoiceSessionStatusType.CONNECTING)

    @classmethod
    def active(cls) -> VoiceSessionStatus:
        return cls(VoiceSessionStatusType.ACTIVE)

    @classmethod
    def paused(cls) -> VoiceSessionStatus:
        return cls(VoiceSessionStatusType.PAUSED)

    @classmethod
    def ended(cls) -> VoiceSessionStatus:
        return cls(VoiceSessionStatusType.ENDED)

    @classmethod
    def failed(cls) -> VoiceSessionStatus:
        return cls(VoiceSessionStatusType.FAILED)
