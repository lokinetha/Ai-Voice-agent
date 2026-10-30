"""
OrganizationCreated Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class OrganizationCreated(DomainEvent):
    """Domain Event published when an Organization aggregate is created.

    Attributes:
        organization_id: OrganizationId string.
        name: Organization name.
        plan_tier: Initial plan tier name.
    """

    organization_id: str = ""
    name: str = ""
    plan_tier: str = ""
