"""
PublishablePlaybookSpec Specification for Playbook Bounded Context.
"""

from __future__ import annotations

from shared.kernel.specification import Specification

from playbook.domain.entities.playbook import Playbook


class PublishablePlaybookSpec(Specification[Playbook]):
    """Specification verifying whether a Playbook meets publishability requirements."""

    def is_satisfied_by(self, candidate: Playbook) -> bool:
        if candidate.status.is_archived:
            return False
        return candidate.validate_publishability().is_success
