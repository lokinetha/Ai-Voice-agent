"""
CreateWorkspace Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import TenantId

from organization.application.dto.organization_dto import WorkspaceDTO
from organization.application.mappers.organization_mapper import OrganizationMapper
from organization.domain.repositories.organization_repository import (
    OrganizationRepository,
)


@dataclass(frozen=True)
class CreateWorkspaceCommand(Command):
    """Command requesting new Workspace creation within an Organization."""

    tenant_id: str
    workspace_name: str


class CreateWorkspaceHandler(CommandHandler[CreateWorkspaceCommand, WorkspaceDTO]):
    """Handler executing CreateWorkspaceCommand."""

    def __init__(
        self,
        organization_repository: OrganizationRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._org_repo = organization_repository
        self._uow = unit_of_work

    async def handle(self, command: CreateWorkspaceCommand) -> Result[WorkspaceDTO]:
        """Execute Workspace creation within plan limits.

        Args:
            command: CreateWorkspaceCommand instance.

        Returns:
            Result wrapping WorkspaceDTO on success, or Error on failure.
        """
        if not command.workspace_name or not command.workspace_name.strip():
            return Result.fail(Error("VALIDATION_ERROR", "Workspace name cannot be empty"))

        org = await self._org_repo.get_by_tenant(TenantId(command.tenant_id))
        if org is None:
            return Result.fail(Error("NOT_FOUND", f"Organization for tenant {command.tenant_id} not found"))

        # Domain Aggregate method enforces invariant workspace_count <= plan.max_workspaces
        ws_result = org.create_workspace(name=command.workspace_name)
        if ws_result.is_failure:
            return Result.fail(ws_result.error)

        workspace = ws_result.value

        async with self._uow:
            await self._org_repo.save(org)
            await self._uow.commit()

        return Result.ok(OrganizationMapper.to_workspace_dto(workspace))
