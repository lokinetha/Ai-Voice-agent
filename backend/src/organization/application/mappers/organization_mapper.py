"""
OrganizationMapper for mapping between Domain Aggregates and Application DTOs.
"""

from __future__ import annotations

from organization.application.dto.organization_dto import (
    OrganizationDTO,
    PlanDTO,
    WorkspaceDTO,
)
from organization.domain.entities.organization import Organization
from organization.domain.entities.workspace import Workspace
from organization.domain.value_objects.plan import Plan


class OrganizationMapper:
    """Static mapper for Organization Aggregate Root ↔ DTO conversion."""

    @staticmethod
    def to_dto(org: Organization) -> OrganizationDTO:
        """Map Organization aggregate to OrganizationDTO."""
        return OrganizationDTO(
            id=str(org.id.value),
            tenant_id=str(org.tenant_id.value),
            name=org.name,
            plan=OrganizationMapper.to_plan_dto(org.plan),
            billing_email=org.billing_info.billing_email.value,
            workspaces=tuple(OrganizationMapper.to_workspace_dto(w) for w in org.workspaces),
            created_at=org.created_at.value,
        )

    @staticmethod
    def to_workspace_dto(workspace: Workspace) -> WorkspaceDTO:
        """Map Workspace entity to WorkspaceDTO."""
        return WorkspaceDTO(
            id=str(workspace.id.value),
            name=workspace.name,
            status=workspace.status,
            created_at=workspace.created_at.value,
        )

    @staticmethod
    def to_plan_dto(plan: Plan) -> PlanDTO:
        """Map Plan value object to PlanDTO."""
        return PlanDTO(
            tier=plan.tier.value,
            max_agents=plan.max_agents,
            max_minutes_per_month=plan.max_minutes_per_month,
            max_kb_documents=plan.max_kb_documents,
            max_workspaces=plan.max_workspaces,
            price_cents=plan.price.amount,
            currency=plan.price.currency,
        )
