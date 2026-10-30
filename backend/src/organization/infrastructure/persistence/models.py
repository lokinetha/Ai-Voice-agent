"""
SQLAlchemy 2.x Persistence Models for Organization Bounded Context.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class OrgBase(DeclarativeBase):
    """Declarative Base for Organization models."""



class OrganizationModel(OrgBase):
    """SQLAlchemy ORM Model mapping 'organizations' table."""

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Plan details
    plan_tier: Mapped[str] = mapped_column(String(50), nullable=False, default="FREE")
    plan_max_agents: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    plan_max_minutes_per_month: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    plan_max_kb_documents: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    plan_max_workspaces: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    plan_price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    plan_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Billing
    billing_email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Settings
    default_language: Mapped[str] = mapped_column(String(10), nullable=False, default="en-US")
    region: Mapped[str] = mapped_column(String(50), nullable=False, default="us-east-1")
    compliance_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationship to Workspace children
    workspaces: Mapped[list[WorkspaceModel]] = relationship(
        "WorkspaceModel", back_populates="organization", cascade="all, delete-orphan", lazy="selectin"
    )


class WorkspaceModel(OrgBase):
    """SQLAlchemy ORM Model mapping 'workspaces' table."""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    organization: Mapped[OrganizationModel] = relationship("OrganizationModel", back_populates="workspaces")
