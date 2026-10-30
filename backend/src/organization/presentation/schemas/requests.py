"""
Pydantic Request Schemas for Organization Presentation Layer.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class CreateOrganizationRequest(BaseModel):
    """HTTP Request schema for creating a new Organization."""

    name: str = Field(..., description="Organization name", examples=["Acme Telesales Inc."])
    billing_email: EmailStr = Field(..., description="Primary billing email", examples=["billing@acme.com"])
    tenant_id: str | None = Field(default=None, description="Optional tenant boundary ID")


class CreateWorkspaceRequest(BaseModel):
    """HTTP Request schema for creating a new Workspace within Organization."""

    workspace_name: str = Field(..., description="Name for new workspace", examples=["Sales Outbound"])


class ChangePlanRequest(BaseModel):
    """HTTP Request schema for changing Organization subscription plan tier."""

    target_plan_tier: str = Field(..., description="Target plan tier (FREE, PRO, ENTERPRISE)", examples=["PRO"])
