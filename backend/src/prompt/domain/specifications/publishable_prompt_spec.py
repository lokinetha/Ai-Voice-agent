"""
PublishablePromptSpec Specification for Prompt Bounded Context.
"""

from __future__ import annotations

from shared.kernel.specification import Specification

from prompt.domain.entities.prompt import Prompt


class PublishablePromptSpec(Specification[Prompt]):
    """Specification verifying whether a Prompt is in a publishable state."""

    def is_satisfied_by(self, candidate: Prompt) -> bool:
        if candidate.status.is_archived:
            return False
        if not candidate.compiled_prompt_text or not candidate.compiled_prompt_text.strip():
            return False
        if candidate.compilation_metadata is None:
            return False
        return True
