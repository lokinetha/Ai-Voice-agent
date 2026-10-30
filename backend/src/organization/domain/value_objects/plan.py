"""
Plan Value Object for Organization Bounded Context.

Defines subscription plan tiers and resource limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shared.kernel.value_object import ValueObject
from shared.kernel.value_objects import MoneyAmount


class PlanTier(StrEnum):
    """Enumeration of subscription plan tiers."""

    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


@dataclass(frozen=True)
class Plan(ValueObject):
    """Plan Value Object encapsulating subscription limits and pricing."""

    tier: PlanTier
    max_agents: int
    max_minutes_per_month: int
    max_kb_documents: int
    max_workspaces: int
    price: MoneyAmount

    def _validate(self) -> None:
        if not isinstance(self.tier, PlanTier):
            raise ValueError(f"Invalid plan tier: {self.tier}")
        if self.max_agents < 1:
            raise ValueError("max_agents must be >= 1")
        if self.max_minutes_per_month < 0:
            raise ValueError("max_minutes_per_month cannot be negative")
        if self.max_kb_documents < 0:
            raise ValueError("max_kb_documents cannot be negative")
        if self.max_workspaces < 1:
            raise ValueError("max_workspaces must be >= 1")

    @classmethod
    def free(cls) -> Plan:
        """Construct default FREE tier plan."""
        return cls(
            tier=PlanTier.FREE,
            max_agents=2,
            max_minutes_per_month=100,
            max_kb_documents=10,
            max_workspaces=1,
            price=MoneyAmount(0, "USD"),
        )

    @classmethod
    def pro(cls) -> Plan:
        """Construct default PRO tier plan."""
        return cls(
            tier=PlanTier.PRO,
            max_agents=10,
            max_minutes_per_month=2000,
            max_kb_documents=100,
            max_workspaces=5,
            price=MoneyAmount(4900, "USD"),  # $49.00
        )

    @classmethod
    def enterprise(cls) -> Plan:
        """Construct default ENTERPRISE tier plan."""
        return cls(
            tier=PlanTier.ENTERPRISE,
            max_agents=100,
            max_minutes_per_month=50000,
            max_kb_documents=5000,
            max_workspaces=50,
            price=MoneyAmount(49900, "USD"),  # $499.00
        )
