"""
CommunicationStyle Value Object.

Describes HOW the agent should communicate — tone, formality, and pacing.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


class ToneType(enum.Enum):
    """Communication tone enumeration."""

    PROFESSIONAL = "PROFESSIONAL"
    FRIENDLY = "FRIENDLY"
    EMPATHETIC = "EMPATHETIC"
    ASSERTIVE = "ASSERTIVE"
    CASUAL = "CASUAL"


class FormalityLevel(enum.Enum):
    """Formality level enumeration."""

    FORMAL = "FORMAL"
    SEMI_FORMAL = "SEMI_FORMAL"
    INFORMAL = "INFORMAL"


class PacingType(enum.Enum):
    """Response pacing enumeration."""

    SLOW = "SLOW"
    MODERATE = "MODERATE"
    FAST = "FAST"


@dataclass(frozen=True)
class CommunicationStyle(ValueObject):
    """Immutable value object defining agent communication parameters.

    Attributes:
        tone: Primary communication tone.
        formality: Level of formality.
        pacing: Response pacing speed.
        vocabulary_level: Target vocabulary complexity (1=simple, 5=expert).
        use_filler_words: Whether to inject natural speech fillers.
    """

    tone: ToneType = ToneType.PROFESSIONAL
    formality: FormalityLevel = FormalityLevel.SEMI_FORMAL
    pacing: PacingType = PacingType.MODERATE
    vocabulary_level: int = 3
    use_filler_words: bool = False

    def _validate(self) -> None:
        if not 1 <= self.vocabulary_level <= 5:
            raise ValueError("vocabulary_level must be between 1 and 5")

    @classmethod
    def default(cls) -> CommunicationStyle:
        return cls()
