"""
OrganizationRepository Domain Interface for Organization Bounded Context.

Extends generic Repository interface for Organization aggregate root persistence operations.
"""

from __future__ import annotations

from abc import abstractmethod

from shared.kernel.repository import Repository
from shared.kernel.value_objects import OrganizationId, TenantId, WorkspaceId

from organization.domain.entities.organization import Organization


class OrganizationRepository(Repository[Organization, OrganizationId]):
    """Domain Repository Interface for Organization Aggregate Root."""

    @abstractmethod
    async def get_by_tenant(self, tenant_id: TenantId) -> Organization | None:
        """Find Organization by TenantId boundary.

        Args:
            tenant_id: TenantId value object.

        Returns:
            Organization aggregate root if found, or None.
        """
        ...

    @abstractmethod
    async def get_by_workspace_id(self, workspace_id: WorkspaceId) -> Organization | None:
        """Find Organization containing target WorkspaceId.

        Args:
            workspace_id: WorkspaceId value object.

        Returns:
            Organization aggregate root if found, or None.
        """
        ...
