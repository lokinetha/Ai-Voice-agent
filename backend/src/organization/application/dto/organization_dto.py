"""
Organization Data Transfer Objects (DTOs) for Application Layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WorkspaceDTO:
    """DTO representing a Workspace entity."""

    id: str
    name: str
    status: str
    created_at: datetime


@dataclass(frozen=True)
class PlanDTO:
    """DTO representing a Plan value object."""

    tier: str
    max_agents: int
    max_minutes_per_month: int
    max_kb_documents: int
    max_workspaces: int
    price_cents: int
    currency: str


@dataclass(frozen=True)
class OrganizationDTO:
    """DTO representing an Organization aggregate root."""

    id: str
    tenant_id: str
    name: str
    plan: PlanDTO
    billing_email: str
    workspaces: tuple[WorkspaceDTO, ...]
    created_at: datetime
