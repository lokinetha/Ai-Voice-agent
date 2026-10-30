"""
OrgSettings Value Object for Organization Bounded Context.

Encapsulates global compliance, language, and retention preferences.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject
from shared.kernel.value_objects import Language, Region


@dataclass(frozen=True)
class OrgSettings(ValueObject):
    """OrgSettings Value Object."""

    default_language: Language
    region: Region
    compliance_mode: bool = False
    retention_days: int = 90

    def _validate(self) -> None:
        if self.retention_days < 1:
            raise ValueError("retention_days must be >= 1")

    @classmethod
    def default(cls) -> OrgSettings:
        """Construct default OrgSettings."""
        return cls(
            default_language=Language("en-US"),
            region=Region("us-east-1"),
            compliance_mode=False,
            retention_days=90,
        )
