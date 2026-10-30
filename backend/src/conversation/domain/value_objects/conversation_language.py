"""
ConversationLanguage Value Object for Conversation Bounded Context.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class ConversationLanguage(ValueObject):
    """ConversationLanguage Value Object storing BCP 47 language tag."""

    code: str

    def _validate(self) -> None:
        pattern = r"^[a-z]{2}(-[A-Z]{2})?$"
        if not self.code or not re.match(pattern, self.code):
            raise ValueError(f"Invalid BCP 47 language tag: {self.code}")

    @classmethod
    def default(cls) -> ConversationLanguage:
        return cls(code="en-US")
