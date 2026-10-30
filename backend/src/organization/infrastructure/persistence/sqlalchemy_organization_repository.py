"""
SQLAlchemy 2.x Repository Implementation for Organization Aggregate Root.

Implements OrganizationRepository domain interface using async SQLAlchemy sessions.
"""

from __future__ import annotations

from datetime import UTC

from shared.kernel.specification import Specification
from shared.kernel.value_objects import (
    Email,
    Language,
    MoneyAmount,
    OrganizationId,
    Region,
    TenantId,
    Timestamp,
    WorkspaceId,
)
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from organization.domain.entities.organization import Organization
from organization.domain.entities.workspace import Workspace
from organization.domain.repositories.organization_repository import (
    OrganizationRepository,
)
from organization.domain.value_objects.billing_info import BillingInfo
from organization.domain.value_objects.org_settings import OrgSettings
from organization.domain.value_objects.plan import Plan, PlanTier
from organization.infrastructure.persistence.models import (
    OrganizationModel,
    WorkspaceModel,
)


class SqlAlchemyOrganizationRepository(OrganizationRepository):
    """SQLAlchemy implementation of OrganizationRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: OrganizationId) -> Organization | None:
        """Retrieve Organization aggregate by ID."""
        stmt = select(OrganizationModel).where(OrganizationModel.id == str(id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def get_by_tenant(self, tenant_id: TenantId) -> Organization | None:
        """Retrieve Organization aggregate by TenantId."""
        stmt = select(OrganizationModel).where(OrganizationModel.tenant_id == str(tenant_id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def get_by_workspace_id(self, workspace_id: WorkspaceId) -> Organization | None:
        """Retrieve Organization aggregate containing workspace_id."""
        stmt = (
            select(OrganizationModel)
            .join(WorkspaceModel)
            .where(WorkspaceModel.id == str(workspace_id.value))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def save(self, aggregate: Organization) -> None:
        """Persist or update Organization aggregate root and workspace child entities."""
        stmt = select(OrganizationModel).where(OrganizationModel.id == str(aggregate.id.value))
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = OrganizationModel(
                id=str(aggregate.id.value),
                tenant_id=str(aggregate.tenant_id.value),
                name=aggregate.name,
                plan_tier=aggregate.plan.tier.value,
                plan_max_agents=aggregate.plan.max_agents,
                plan_max_minutes_per_month=aggregate.plan.max_minutes_per_month,
                plan_max_kb_documents=aggregate.plan.max_kb_documents,
                plan_max_workspaces=aggregate.plan.max_workspaces,
                plan_price_cents=aggregate.plan.price.amount,
                plan_currency=aggregate.plan.price.currency,
                billing_email=aggregate.billing_info.billing_email.value,
                default_language=aggregate.settings.default_language.code,
                region=aggregate.settings.region.value,
                compliance_mode=aggregate.settings.compliance_mode,
                retention_days=aggregate.settings.retention_days,
                created_at=aggregate.created_at.value,
                workspaces=[
                    WorkspaceModel(
                        id=str(w.id.value),
                        org_id=str(aggregate.id.value),
                        name=w.name,
                        status=w.status,
                        created_at=w.created_at.value,
                    )
                    for w in aggregate.workspaces
                ],
            )
            self._session.add(model)
        else:
            existing.name = aggregate.name
            existing.plan_tier = aggregate.plan.tier.value
            existing.plan_max_agents = aggregate.plan.max_agents
            existing.plan_max_minutes_per_month = aggregate.plan.max_minutes_per_month
            existing.plan_max_kb_documents = aggregate.plan.max_kb_documents
            existing.plan_max_workspaces = aggregate.plan.max_workspaces
            existing.plan_price_cents = aggregate.plan.price.amount
            existing.plan_currency = aggregate.plan.price.currency
            existing.billing_email = aggregate.billing_info.billing_email.value
            existing.default_language = aggregate.settings.default_language.code
            existing.region = aggregate.settings.region.value
            existing.compliance_mode = aggregate.settings.compliance_mode
            existing.retention_days = aggregate.settings.retention_days

            # Update workspaces child collection
            existing_ws_ids = {w.id for w in existing.workspaces}
            target_ws_dict = {str(w.id.value): w for w in aggregate.workspaces}

            # Add or update
            for ws_id_str, ws_entity in target_ws_dict.items():
                if ws_id_str not in existing_ws_ids:
                    existing.workspaces.append(
                        WorkspaceModel(
                            id=ws_id_str,
                            org_id=str(aggregate.id.value),
                            name=ws_entity.name,
                            status=ws_entity.status,
                            created_at=ws_entity.created_at.value,
                        )
                    )
                else:
                    for w_model in existing.workspaces:
                        if w_model.id == ws_id_str:
                            w_model.name = ws_entity.name
                            w_model.status = ws_entity.status

    async def delete(self, aggregate: Organization) -> None:
        """Delete Organization aggregate from persistence."""
        stmt = sql_delete(OrganizationModel).where(OrganizationModel.id == str(aggregate.id.value))
        await self._session.execute(stmt)

    async def find(self, spec: Specification[Organization]) -> list[Organization]:
        """Find Organization aggregates satisfying specification filter."""
        stmt = select(OrganizationModel)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        aggregates = [self._to_aggregate(m) for m in models]
        return [a for a in aggregates if spec.is_satisfied_by(a)]

    async def count(self, spec: Specification[Organization]) -> int:
        """Count Organization aggregates satisfying specification filter."""
        aggregates = await self.find(spec)
        return len(aggregates)

    @staticmethod
    def _to_aggregate(model: OrganizationModel) -> Organization:
        """Map ORM OrganizationModel to domain Organization aggregate root."""
        created_at_dt = model.created_at
        if created_at_dt and created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=UTC)

        plan = Plan(
            tier=PlanTier(model.plan_tier),
            max_agents=model.plan_max_agents,
            max_minutes_per_month=model.plan_max_minutes_per_month,
            max_kb_documents=model.plan_max_kb_documents,
            max_workspaces=model.plan_max_workspaces,
            price=MoneyAmount(model.plan_price_cents, model.plan_currency),
        )

        billing_info = BillingInfo(billing_email=Email(model.billing_email))
        settings = OrgSettings(
            default_language=Language(model.default_language),
            region=Region(model.region),
            compliance_mode=model.compliance_mode,
            retention_days=model.retention_days,
        )

        workspaces = [
            Workspace(
                id=WorkspaceId(w.id),
                name=w.name,
                status=w.status,
                created_at=Timestamp(w.created_at.replace(tzinfo=UTC) if w.created_at.tzinfo is None else w.created_at),
            )
            for w in model.workspaces
        ]

        return Organization(
            id=OrganizationId(model.id),
            tenant_id=TenantId(model.tenant_id),
            name=model.name,
            plan=plan,
            billing_info=billing_info,
            settings=settings,
            workspaces=workspaces,
            created_at=Timestamp(created_at_dt),
        )
