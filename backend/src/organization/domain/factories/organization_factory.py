"""
OrganizationFactory for Organization Bounded Context.

Encapsulates Organization aggregate root construction with default Workspace creation and event publishing.
"""

from __future__ import annotations

from shared.kernel.value_objects import (
    Email,
    OrganizationId,
    TenantId,
)

from organization.domain.entities.organization import Organization
from organization.domain.events.organization_created import OrganizationCreated
from organization.domain.value_objects.billing_info import BillingInfo
from organization.domain.value_objects.org_settings import OrgSettings
from organization.domain.value_objects.plan import Plan


class OrganizationFactory:
    """Factory for creating new Organization Aggregate Roots."""

    @classmethod
    def create(
        self,
        name: str,
        billing_email: Email,
        tenant_id: TenantId | None = None,
        org_id: OrganizationId | None = None,
        plan: Plan | None = None,
        default_workspace_name: str = "Default Workspace",
    ) -> Organization:
        """Create and initialize a new Organization aggregate root with default workspace.

        Args:
            name: Organization name.
            billing_email: Primary billing email.
            tenant_id: Optional multi-tenancy TenantId (generates UUID4 if None).
            org_id: Optional explicit OrganizationId.
            plan: Optional initial Plan (defaults to FREE tier if None).
            default_workspace_name: Name for initial workspace entity.

        Returns:
            Initialized Organization aggregate with default workspace and recorded OrganizationCreated event.
        """
        o_id = org_id or OrganizationId()
        t_id = tenant_id or TenantId()
        p = plan or Plan.free()
        b_info = BillingInfo(billing_email=billing_email)
        settings = OrgSettings.default()

        org = Organization(
            id=o_id,
            tenant_id=t_id,
            name=name,
            plan=p,
            billing_info=b_info,
            settings=settings,
            workspaces=(),
        )

        # Create initial default workspace child entity
        org.create_workspace(name=default_workspace_name)

        org._raise_event(
            OrganizationCreated(
                organization_id=str(o_id.value),
                tenant_id=str(t_id.value),
                name=name,
                plan_tier=p.tier.value,
            )
        )

        return org
