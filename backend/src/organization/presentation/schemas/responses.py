"""
Pydantic Response Schemas for Organization Presentation Layer.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PlanResponse(BaseModel):
    """HTTP Response schema representing Organization Plan."""

    tier: str = Field(..., description="Plan tier string")
    max_agents: int = Field(..., description="Max agents quota")
    max_minutes_per_month: int = Field(..., description="Max streaming minutes quota")
    max_kb_documents: int = Field(..., description="Max KB documents quota")
    max_workspaces: int = Field(..., description="Max workspaces quota")
    price_cents: int = Field(..., description="Price in smallest currency unit")
    currency: str = Field(..., description="ISO currency code")


class WorkspaceResponse(BaseModel):
    """HTTP Response schema representing Workspace entity."""

    id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="Workspace name")
    status: str = Field(..., description="Workspace status")
    created_at: datetime = Field(..., description="Creation timestamp")


class OrganizationResponse(BaseModel):
    """HTTP Response schema representing Organization aggregate."""

    id: str = Field(..., description="Organization ID")
    tenant_id: str = Field(..., description="Multi-tenant TenantID")
    name: str = Field(..., description="Organization name")
    plan: PlanResponse = Field(..., description="Active Plan details")
    billing_email: str = Field(..., description="Billing email")
    workspaces: list[WorkspaceResponse] = Field(..., description="Child workspaces")
    created_at: datetime = Field(..., description="Creation timestamp")
