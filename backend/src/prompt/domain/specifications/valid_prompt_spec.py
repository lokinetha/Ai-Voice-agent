"""
ValidPromptSpec Specification for Prompt Bounded Context.
"""

from __future__ import annotations

from shared.kernel.specification import Specification

from prompt.domain.entities.prompt import Prompt


class ValidPromptSpec(Specification[Prompt]):
    """Specification checking overall structural validity of a Prompt."""

    def is_satisfied_by(self, candidate: Prompt) -> bool:
        if not candidate.name or not candidate.name.strip():
            return False
        return True
