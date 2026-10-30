"""
Unit tests for Organization Domain Layer.
"""

from __future__ import annotations

import unittest

from organization.domain.events.organization_created import OrganizationCreated
from organization.domain.events.workspace_created import WorkspaceCreated
from organization.domain.factories.organization_factory import OrganizationFactory
from organization.domain.services.plan_validation_service import PlanValidationService
from organization.domain.value_objects.plan import Plan, PlanTier
from shared.kernel.value_objects import Email, TenantId


class TestOrganizationDomain(unittest.TestCase):
    def test_organization_factory_creation(self) -> None:
        email = Email("billing@enterprise.com")
        tenant_id = TenantId("tenant-org-1")

        org = OrganizationFactory.create(
            name="Enterprise Sales Inc",
            billing_email=email,
            tenant_id=tenant_id,
        )

        self.assertEqual(org.name, "Enterprise Sales Inc")
        self.assertEqual(org.tenant_id, tenant_id)
        self.assertEqual(org.plan.tier, PlanTier.FREE)
        self.assertEqual(len(org.workspaces), 1)  # Default workspace
        self.assertEqual(org.workspaces[0].name, "Default Workspace")

        events = org.domain_events
        self.assertEqual(len(events), 2)  # WorkspaceCreated + OrganizationCreated
        self.assertTrue(any(isinstance(e, OrganizationCreated) for e in events))
        self.assertTrue(any(isinstance(e, WorkspaceCreated) for e in events))

    def test_workspace_limit_invariant(self) -> None:
        org = OrganizationFactory.create(
            name="Limit Test Org",
            billing_email=Email("limit@test.com"),
            plan=Plan.free(),  # max_workspaces = 1
        )
        self.assertEqual(len(org.workspaces), 1)

        # Attempt to create 2nd workspace under FREE plan (limit = 1)
        res = org.create_workspace("Secondary Workspace")
        self.assertTrue(res.is_failure)
        self.assertEqual(res.error.code, "LIMIT_EXCEEDED")

    def test_change_plan_upgrade_and_downgrade(self) -> None:
        org = OrganizationFactory.create(
            name="Plan Test Org",
            billing_email=Email("plan@test.com"),
            plan=Plan.free(),
        )

        # Upgrade to PRO
        res_pro = org.change_plan(Plan.pro())
        self.assertTrue(res_pro.is_success)
        self.assertEqual(org.plan.tier, PlanTier.PRO)

        # Now create 2 additional workspaces under PRO (limit = 5)
        res_ws2 = org.create_workspace("Workspace 2")
        res_ws3 = org.create_workspace("Workspace 3")
        self.assertTrue(res_ws2.is_success)
        self.assertTrue(res_ws3.is_success)
        self.assertEqual(len(org.workspaces), 3)

        # Attempt to downgrade to FREE (limit = 1) while owning 3 workspaces -> INVARIANT_VIOLATION
        res_down = org.change_plan(Plan.free())
        self.assertTrue(res_down.is_failure)
        self.assertEqual(res_down.error.code, "INVARIANT_VIOLATION")

    def test_plan_validation_service(self) -> None:
        service = PlanValidationService()
        org = OrganizationFactory.create(
            name="Quota Org",
            billing_email=Email("quota@test.com"),
            plan=Plan.free(),  # max_agents = 2
        )

        self.assertTrue(service.validate_agent_creation(org, current_agent_count=1).is_success)
        self.assertTrue(service.validate_agent_creation(org, current_agent_count=2).is_failure)


if __name__ == "__main__":
    unittest.main()
