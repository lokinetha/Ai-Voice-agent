"""
ChangePlan Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import TenantId

from organization.application.dto.organization_dto import OrganizationDTO
from organization.application.mappers.organization_mapper import OrganizationMapper
from organization.domain.repositories.organization_repository import (
    OrganizationRepository,
)
from organization.domain.value_objects.plan import Plan, PlanTier


@dataclass(frozen=True)
class ChangePlanCommand(Command):
    """Command requesting subscription plan tier change."""

    tenant_id: str
    target_plan_tier: str  # FREE, PRO, ENTERPRISE


class ChangePlanHandler(CommandHandler[ChangePlanCommand, OrganizationDTO]):
    """Handler executing ChangePlanCommand."""

    def __init__(
        self,
        organization_repository: OrganizationRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._org_repo = organization_repository
        self._uow = unit_of_work

    async def handle(self, command: ChangePlanCommand) -> Result[OrganizationDTO]:
        """Execute plan change.

        Args:
            command: ChangePlanCommand instance.

        Returns:
            Result wrapping updated OrganizationDTO on success, or Error on failure.
        """
        try:
            tier_enum = PlanTier(command.target_plan_tier.upper())
        except ValueError:
            return Result.fail(Error("VALIDATION_ERROR", f"Invalid plan tier: {command.target_plan_tier}"))

        target_plan = {
            PlanTier.FREE: Plan.free(),
            PlanTier.PRO: Plan.pro(),
            PlanTier.ENTERPRISE: Plan.enterprise(),
        }[tier_enum]

        org = await self._org_repo.get_by_tenant(TenantId(command.tenant_id))
        if org is None:
            return Result.fail(Error("NOT_FOUND", f"Organization for tenant {command.tenant_id} not found"))

        # Domain Aggregate method enforces invariant workspace_count <= target_plan.max_workspaces
        change_res = org.change_plan(target_plan)
        if change_res.is_failure:
            return Result.fail(change_res.error)

        async with self._uow:
            await self._org_repo.save(org)
            await self._uow.commit()

        return Result.ok(OrganizationMapper.to_dto(org))
