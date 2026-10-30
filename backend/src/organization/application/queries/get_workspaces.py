"""
GetWorkspaces Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import TenantId

from organization.application.dto.organization_dto import WorkspaceDTO
from organization.application.mappers.organization_mapper import OrganizationMapper
from organization.domain.repositories.organization_repository import (
    OrganizationRepository,
)


@dataclass(frozen=True)
class GetWorkspacesQuery(Query):
    """Query requesting Workspaces list by tenant_id."""

    tenant_id: str


class GetWorkspacesHandler(
    QueryHandler[GetWorkspacesQuery, tuple[WorkspaceDTO, ...]]
):
    """Handler executing GetWorkspacesQuery."""

    def __init__(self, organization_repository: OrganizationRepository) -> None:
        self._org_repo = organization_repository

    async def handle(self, query: GetWorkspacesQuery) -> Result[tuple[WorkspaceDTO, ...]]:
        """Execute GetWorkspacesQuery."""
        if not query.tenant_id:
            return Result.fail(Error("VALIDATION_ERROR", "Tenant ID cannot be empty"))

        org = await self._org_repo.get_by_tenant(TenantId(query.tenant_id))
        if org is None:
            return Result.fail(Error("NOT_FOUND", f"Organization for tenant '{query.tenant_id}' not found"))

        dtos = tuple(OrganizationMapper.to_workspace_dto(w) for w in org.workspaces)
        return Result.ok(dtos)
