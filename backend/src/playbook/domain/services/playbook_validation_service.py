"""
PlaybookValidationService Domain Service for Playbook Bounded Context.

Validates structural integrity and publishability of Playbooks across stages,
goals, transitions, rules, and persona definitions.
"""

from __future__ import annotations

from shared.kernel.domain_service import DomainService
from shared.kernel.result import Error, Result

from playbook.domain.entities.playbook import Playbook
from playbook.domain.specifications.publishable_playbook_spec import (
    PublishablePlaybookSpec,
)
from playbook.domain.specifications.valid_playbook_spec import ValidPlaybookSpec


class PlaybookValidationService(DomainService):
    """Domain Service validating Playbook integrity and publishability."""

    def __init__(self) -> None:
        self._valid_spec = ValidPlaybookSpec()
        self._publishable_spec = PublishablePlaybookSpec()

    def validate_playbook(self, playbook: Playbook) -> Result[None]:
        """Perform comprehensive validation on a Playbook.

        Args:
            playbook: Playbook aggregate root.

        Returns:
            Result indicating success or VALIDATION_ERROR.
        """
        if not self._valid_spec.is_satisfied_by(playbook):
            return Result.fail(Error("VALIDATION_ERROR", "Playbook fails basic validity check"))

        return Result.ok(None)

    def can_publish(self, playbook: Playbook) -> bool:
        """Check whether a Playbook can be published.

        Args:
            playbook: Playbook aggregate root.

        Returns:
            True if publishable.
        """
        return self._publishable_spec.is_satisfied_by(playbook)
