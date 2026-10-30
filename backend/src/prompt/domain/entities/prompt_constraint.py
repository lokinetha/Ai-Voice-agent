"""
PromptConstraint Entity for Prompt Bounded Context.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class PromptConstraint(Entity[EntityId]):
    """Constraint entity enforcing strict negative or behavioral rules."""

    def __init__(
        self,
        id: EntityId,
        constraint_type: str,
        rule_text: str,
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not constraint_type or not constraint_type.strip():
            raise ValueError("PromptConstraint constraint_type cannot be empty")
        if not rule_text or not rule_text.strip():
            raise ValueError("PromptConstraint rule_text cannot be empty")

        self._constraint_type = constraint_type.strip()
        self._rule_text = rule_text.strip()

    @property
    def constraint_type(self) -> str:
        return self._constraint_type

    @property
    def rule_text(self) -> str:
        return self._rule_text
