"""
Unit tests for Organization Application Command and Query Handlers.
"""

from __future__ import annotations

import asyncio
import unittest

from organization.application.commands.change_plan import (
    ChangePlanCommand,
    ChangePlanHandler,
)
from organization.application.commands.create_organization import (
    CreateOrganizationCommand,
    CreateOrganizationHandler,
)
from organization.application.commands.create_workspace import (
    CreateWorkspaceCommand,
    CreateWorkspaceHandler,
)
from organization.application.queries.get_organization import (
    GetOrganizationHandler,
    GetOrganizationQuery,
)
from organization.application.queries.get_workspaces import (
    GetWorkspacesHandler,
    GetWorkspacesQuery,
)
from organization.domain.entities.organization import Organization
from organization.domain.repositories.organization_repository import (
    OrganizationRepository,
)
from shared.kernel.domain_event import DomainEvent
from shared.kernel.specification import Specification
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import OrganizationId, TenantId, WorkspaceId


class InMemoryOrganizationRepository(OrganizationRepository):
    def __init__(self) -> None:
        self.orgs: dict[str, Organization] = {}

    async def get_by_id(self, id: OrganizationId) -> Organization | None:
        return self.orgs.get(str(id.value))

    async def get_by_tenant(self, tenant_id: TenantId) -> Organization | None:
        for o in self.orgs.values():
            if o.tenant_id == tenant_id:
                return o
        return None

    async def get_by_workspace_id(self, workspace_id: WorkspaceId) -> Organization | None:
        for o in self.orgs.values():
            if any(w.id == workspace_id for w in o.workspaces):
                return o
        return None

    async def save(self, aggregate: Organization) -> None:
        self.orgs[str(aggregate.id.value)] = aggregate

    async def delete(self, aggregate: Organization) -> None:
        self.orgs.pop(str(aggregate.id.value), None)

    async def find(self, spec: Specification[Organization]) -> list[Organization]:
        return [o for o in self.orgs.values() if spec.is_satisfied_by(o)]

    async def count(self, spec: Specification[Organization]) -> int:
        return len(await self.find(spec))


class DummyUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.committed = False

    async def __aenter__(self) -> DummyUnitOfWork:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass

    def collect_events(self) -> list[DomainEvent]:
        return []


class TestOrganizationApplicationHandlers(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryOrganizationRepository()
        self.uow = DummyUnitOfWork()

    def test_create_organization_success(self) -> None:
        async def run() -> None:
            handler = CreateOrganizationHandler(self.repo, self.uow)
            cmd = CreateOrganizationCommand(
                name="Acme Corp",
                billing_email="billing@acme.com",
                tenant_id="t-acme-1",
            )
            res = await handler.handle(cmd)
            self.assertTrue(res.is_success)
            self.assertEqual(res.value.name, "Acme Corp")
            self.assertEqual(res.value.plan.tier, "FREE")
            self.assertEqual(len(res.value.workspaces), 1)

        asyncio.run(run())

    def test_create_workspace_success(self) -> None:
        async def run() -> None:
            create_org_h = CreateOrganizationHandler(self.repo, self.uow)
            org_res = await create_org_h.handle(
                CreateOrganizationCommand("Acme", "b@acme.com", "t-ws-1")
            )
            tenant_id = org_res.value.tenant_id

            # Upgrade plan to PRO so we can create more workspaces
            change_plan_h = ChangePlanHandler(self.repo, self.uow)
            await change_plan_h.handle(ChangePlanCommand(tenant_id, "PRO"))

            create_ws_h = CreateWorkspaceHandler(self.repo, self.uow)
            ws_res = await create_ws_h.handle(
                CreateWorkspaceCommand(tenant_id=tenant_id, workspace_name="Outbound Sales")
            )
            self.assertTrue(ws_res.is_success)
            self.assertEqual(ws_res.value.name, "Outbound Sales")

        asyncio.run(run())

    def test_get_organization_and_workspaces_queries(self) -> None:
        async def run() -> None:
            create_org_h = CreateOrganizationHandler(self.repo, self.uow)
            org_res = await create_org_h.handle(
                CreateOrganizationCommand("Query Org", "q@org.com", "t-query-1")
            )
            tenant_id = org_res.value.tenant_id

            get_org_h = GetOrganizationHandler(self.repo)
            res_org = await get_org_h.handle(GetOrganizationQuery(tenant_id=tenant_id))
            self.assertTrue(res_org.is_success)
            self.assertEqual(res_org.value.name, "Query Org")

            get_ws_h = GetWorkspacesHandler(self.repo)
            res_ws = await get_ws_h.handle(GetWorkspacesQuery(tenant_id=tenant_id))
            self.assertTrue(res_ws.is_success)
            self.assertEqual(len(res_ws.value), 1)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
