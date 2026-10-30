"""
PlanChanged Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class PlanChanged(DomainEvent):
    """Domain Event published when an Organization's plan is updated.

    Attributes:
        organization_id: OrganizationId string.
        old_plan_tier: Previous plan tier string.
        new_plan_tier: New plan tier string.
    """

    organization_id: str = ""
    old_plan_tier: str = ""
    new_plan_tier: str = ""
