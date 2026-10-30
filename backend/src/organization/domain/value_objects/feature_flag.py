"""
FeatureFlag Value Object for Organization Bounded Context.

Encapsulates feature flag enablement per tenant.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class FeatureFlag(ValueObject):
    """FeatureFlag Value Object."""

    flag_name: str
    enabled: bool = False
    description: str = ""

    def _validate(self) -> None:
        if not self.flag_name or not isinstance(self.flag_name, str):
            raise ValueError("FeatureFlag flag_name cannot be empty")
