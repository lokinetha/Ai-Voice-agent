"""
PromptVariable Value Object.

Represents a dynamic variable placeholder inside a Prompt section or instruction.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class PromptVariable(ValueObject):
    """Immutable value object for prompt template placeholders.

    Attributes:
        key: Variable name identifier (e.g. "customer_name").
        default_value: Optional default value string if unpopulated.
        description: Description of what this variable represents.
    """

    key: str = ""
    default_value: str = ""
    description: str = ""

    def _validate(self) -> None:
        if not self.key or not self.key.strip():
            raise ValueError("PromptVariable key cannot be empty")
