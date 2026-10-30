"""
GetOrganization Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import TenantId

from organization.application.dto.organization_dto import OrganizationDTO
from organization.application.mappers.organization_mapper import OrganizationMapper
from organization.domain.repositories.organization_repository import (
    OrganizationRepository,
)


@dataclass(frozen=True)
class GetOrganizationQuery(Query):
    """Query requesting Organization details by tenant_id."""

    tenant_id: str


class GetOrganizationHandler(
    QueryHandler[GetOrganizationQuery, OrganizationDTO]
):
    """Handler executing GetOrganizationQuery."""

    def __init__(self, organization_repository: OrganizationRepository) -> None:
        self._org_repo = organization_repository

    async def handle(self, query: GetOrganizationQuery) -> Result[OrganizationDTO]:
        """Execute GetOrganizationQuery."""
        if not query.tenant_id:
            return Result.fail(Error("VALIDATION_ERROR", "Tenant ID cannot be empty"))

        org = await self._org_repo.get_by_tenant(TenantId(query.tenant_id))
        if org is None:
            return Result.fail(Error("NOT_FOUND", f"Organization for tenant '{query.tenant_id}' not found"))

        return Result.ok(OrganizationMapper.to_dto(org))
