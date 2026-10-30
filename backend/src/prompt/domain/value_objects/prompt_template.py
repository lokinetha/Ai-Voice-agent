"""
PromptTemplate Value Object.

Represents a reusable template structure for system prompt compilation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class PromptTemplate(ValueObject):
    """Immutable value object defining compilation template structure.

    Attributes:
        name: Template format name (e.g., "STANDARD_SYSTEM_PROMPT").
        section_order: Ordered tuple of section categories to include.
        prefix: Optional static system header text.
        suffix: Optional static system footer text.
    """

    name: str = "STANDARD_SYSTEM_PROMPT"
    section_order: tuple[str, ...] = field(
        default=(
            "PERSONA",
            "GOALS",
            "RULES",
            "STAGES",
            "OBJECTIONS",
            "EXAMPLES",
            "CONSTRAINTS",
        )
    )
    prefix: str = "System Instructions:\n"
    suffix: str = "\nEnd of Instructions."

    def _validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("PromptTemplate name cannot be empty")
