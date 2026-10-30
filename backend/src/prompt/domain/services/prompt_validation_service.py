"""
PromptValidationService Domain Service for Prompt Bounded Context.

Validates Prompt structural validity and publishability requirements.
"""

from __future__ import annotations

from shared.kernel.domain_service import DomainService
from shared.kernel.result import Error, Result

from prompt.domain.entities.prompt import Prompt
from prompt.domain.specifications.publishable_prompt_spec import (
    PublishablePromptSpec,
)
from prompt.domain.specifications.valid_prompt_spec import ValidPromptSpec


class PromptValidationService(DomainService):
    """Domain Service validating Prompt integrity and publishability."""

    def __init__(self) -> None:
        self._valid_spec = ValidPromptSpec()
        self._publishable_spec = PublishablePromptSpec()

    def validate_prompt(self, prompt: Prompt) -> Result[None]:
        """Validate basic Prompt structural validity."""
        if not self._valid_spec.is_satisfied_by(prompt):
            return Result.fail(Error("VALIDATION_ERROR", "Prompt fails basic validity check"))

        return Result.ok(None)

    def can_publish(self, prompt: Prompt) -> bool:
        """Check whether a Prompt can be published to production."""
        return self._publishable_spec.is_satisfied_by(prompt)
