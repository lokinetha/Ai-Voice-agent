"""
Integration tests for Organization Infrastructure persistence implementation.
"""

from __future__ import annotations

import unittest

from organization.domain.factories.organization_factory import OrganizationFactory
from organization.domain.value_objects.plan import Plan
from shared.kernel.value_objects import Email, TenantId


class TestOrganizationInfrastructure(unittest.TestCase):
    def test_organization_factory_defaults(self) -> None:
        org = OrganizationFactory.create(
            name="Test Org",
            billing_email=Email("test@org.com"),
            tenant_id=TenantId("tenant-test"),
            plan=Plan.pro(),
        )

        self.assertEqual(org.name, "Test Org")
        self.assertEqual(org.plan.max_workspaces, 5)
        self.assertEqual(len(org.workspaces), 1)


if __name__ == "__main__":
    unittest.main()
