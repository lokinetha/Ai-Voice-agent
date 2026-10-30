"""
CreateOrganization Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import Email, TenantId

from organization.application.dto.organization_dto import OrganizationDTO
from organization.application.mappers.organization_mapper import OrganizationMapper
from organization.domain.factories.organization_factory import OrganizationFactory
from organization.domain.repositories.organization_repository import (
    OrganizationRepository,
)


@dataclass(frozen=True)
class CreateOrganizationCommand(Command):
    """Command requesting new Organization aggregate creation."""

    name: str
    billing_email: str
    tenant_id: str | None = None


class CreateOrganizationHandler(
    CommandHandler[CreateOrganizationCommand, OrganizationDTO]
):
    """Handler executing CreateOrganizationCommand."""

    def __init__(
        self,
        organization_repository: OrganizationRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._org_repo = organization_repository
        self._uow = unit_of_work

    async def handle(self, command: CreateOrganizationCommand) -> Result[OrganizationDTO]:
        """Execute Organization creation.

        Args:
            command: CreateOrganizationCommand instance.

        Returns:
            Result wrapping OrganizationDTO on success, or Error on failure.
        """
        try:
            email_vo = Email(command.billing_email)
        except ValueError as e:
            return Result.fail(Error("VALIDATION_ERROR", str(e)))

        t_id = TenantId(command.tenant_id) if command.tenant_id else TenantId()

        # Check if org with tenant_id already exists
        existing = await self._org_repo.get_by_tenant(t_id)
        if existing is not None:
            return Result.fail(Error("CONFLICT", f"Organization for tenant {t_id.value} already exists"))

        # Construct aggregate via factory
        org = OrganizationFactory.create(
            name=command.name,
            billing_email=email_vo,
            tenant_id=t_id,
        )

        async with self._uow:
            await self._org_repo.save(org)
            await self._uow.commit()

        return Result.ok(OrganizationMapper.to_dto(org))
