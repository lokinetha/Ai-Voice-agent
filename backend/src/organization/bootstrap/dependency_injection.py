"""
Organization Bounded Context Dependency Injection Bootstrap.
"""

from __future__ import annotations

from identity.bootstrap.dependency_injection import SqlAlchemyUnitOfWork
from shared.kernel.unit_of_work import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

from organization.application.commands.change_plan import ChangePlanHandler
from organization.application.commands.create_organization import (
    CreateOrganizationHandler,
)
from organization.application.commands.create_workspace import (
    CreateWorkspaceHandler,
)
from organization.application.queries.get_organization import (
    GetOrganizationHandler,
)
from organization.application.queries.get_workspaces import (
    GetWorkspacesHandler,
)
from organization.domain.repositories.organization_repository import (
    OrganizationRepository,
)
from organization.domain.services.plan_validation_service import (
    PlanValidationService,
)
from organization.infrastructure.persistence.sqlalchemy_organization_repository import (
    SqlAlchemyOrganizationRepository,
)


class OrganizationContainer:
    """Dependency Container for Organization Context services and handlers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._org_repository: OrganizationRepository = (
            SqlAlchemyOrganizationRepository(session)
        )
        self._plan_validation_service = PlanValidationService()
        self._uow: UnitOfWork = SqlAlchemyUnitOfWork(session)

    @property
    def organization_repository(self) -> OrganizationRepository:
        return self._org_repository

    @property
    def plan_validation_service(self) -> PlanValidationService:
        return self._plan_validation_service

    @property
    def unit_of_work(self) -> UnitOfWork:
        return self._uow

    def get_create_organization_handler(self) -> CreateOrganizationHandler:
        return CreateOrganizationHandler(
            organization_repository=self._org_repository,
            unit_of_work=self._uow,
        )

    def get_create_workspace_handler(self) -> CreateWorkspaceHandler:
        return CreateWorkspaceHandler(
            organization_repository=self._org_repository,
            unit_of_work=self._uow,
        )

    def get_change_plan_handler(self) -> ChangePlanHandler:
        return ChangePlanHandler(
            organization_repository=self._org_repository,
            unit_of_work=self._uow,
        )

    def get_organization_handler(self) -> GetOrganizationHandler:
        return GetOrganizationHandler(
            organization_repository=self._org_repository,
        )

    def get_workspaces_handler(self) -> GetWorkspacesHandler:
        return GetWorkspacesHandler(
            organization_repository=self._org_repository,
        )
