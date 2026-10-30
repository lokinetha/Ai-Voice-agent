"""
PromptVersionInfo Value Object.

Captures version metadata for published Prompt versions.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class PromptVersionInfo(ValueObject):
    """Immutable version metadata for a Prompt.

    Attributes:
        version_number: Monotonic version number (1, 2, ...).
        label: Optional human-readable version label (e.g. "v1.0-prod").
        changelog: Description of prompt changes.
    """

    version_number: int = 1
    label: str = ""
    changelog: str = ""

    def _validate(self) -> None:
        if self.version_number < 1:
            raise ValueError("version_number must be >= 1")

    def next(self, label: str = "", changelog: str = "") -> PromptVersionInfo:
        """Increment version number for next published version."""
        return PromptVersionInfo(
            version_number=self.version_number + 1,
            label=label,
            changelog=changelog,
        )
