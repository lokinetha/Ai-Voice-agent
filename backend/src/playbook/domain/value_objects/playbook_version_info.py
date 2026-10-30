"""
PlaybookVersionInfo Value Object.

Captures immutable metadata for a published Playbook version snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class PlaybookVersionInfo(ValueObject):
    """Immutable metadata for a published Playbook version.

    Attributes:
        version_number: Monotonically increasing human-readable version.
        label: Optional human-readable label (e.g. "v2.1-sales").
        changelog: Description of changes from the prior version.
    """

    version_number: int = 1
    label: str = ""
    changelog: str = ""

    def _validate(self) -> None:
        if self.version_number < 1:
            raise ValueError("version_number must be >= 1")

    def next(self, label: str = "", changelog: str = "") -> PlaybookVersionInfo:
        """Create the next sequential version info."""
        return PlaybookVersionInfo(
            version_number=self.version_number + 1,
            label=label,
            changelog=changelog,
        )
