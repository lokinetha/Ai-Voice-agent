"""
ValidPlaybookSpec Specification for Playbook Bounded Context.
"""

from __future__ import annotations

from shared.kernel.specification import Specification

from playbook.domain.entities.playbook import Playbook


class ValidPlaybookSpec(Specification[Playbook]):
    """Specification verifying overall Playbook structural validity."""

    def is_satisfied_by(self, candidate: Playbook) -> bool:
        if not candidate.name or not candidate.name.strip():
            return False
        return True
