"""
SQLAlchemy 2.x Persistence Models for Playbook Bounded Context.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class PlaybookBase(DeclarativeBase):
    """Declarative Base for Playbook models."""

    pass


class PlaybookModel(PlaybookBase):
    """SQLAlchemy ORM Model mapping 'playbooks' table."""

    __tablename__ = "playbooks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")

    # Version Info
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    version_label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    version_changelog: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Value Objects stored as JSON
    persona_json: Mapped[dict[str, Any] | None] = mapped_column("persona", JSON, nullable=True)
    communication_style_json: Mapped[dict[str, Any] | None] = mapped_column(
        "communication_style", JSON, nullable=True
    )
    success_criteria_json: Mapped[dict[str, Any] | None] = mapped_column(
        "success_criteria", JSON, nullable=True
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    goals: Mapped[list[PlaybookGoalModel]] = relationship(
        "PlaybookGoalModel",
        back_populates="playbook",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    stages: Mapped[list[PlaybookStageModel]] = relationship(
        "PlaybookStageModel",
        back_populates="playbook",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PlaybookStageModel.order",
    )
    rules: Mapped[list[PlaybookRuleModel]] = relationship(
        "PlaybookRuleModel",
        back_populates="playbook",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    objections: Mapped[list[PlaybookObjectionModel]] = relationship(
        "PlaybookObjectionModel",
        back_populates="playbook",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    examples: Mapped[list[PlaybookExampleModel]] = relationship(
        "PlaybookExampleModel",
        back_populates="playbook",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    transitions: Mapped[list[PlaybookTransitionModel]] = relationship(
        "PlaybookTransitionModel",
        back_populates="playbook",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PlaybookGoalModel(PlaybookBase):
    """SQLAlchemy ORM Model mapping 'playbook_goals' table."""

    __tablename__ = "playbook_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    playbook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    playbook: Mapped[PlaybookModel] = relationship("PlaybookModel", back_populates="goals")


class PlaybookStageModel(PlaybookBase):
    """SQLAlchemy ORM Model mapping 'playbook_stages' table."""

    __tablename__ = "playbook_stages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    playbook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    playbook: Mapped[PlaybookModel] = relationship("PlaybookModel", back_populates="stages")


class PlaybookRuleModel(PlaybookBase):
    """SQLAlchemy ORM Model mapping 'playbook_rules' table."""

    __tablename__ = "playbook_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    playbook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    condition: Mapped[str] = mapped_column(Text, nullable=False, default="")
    action: Mapped[str] = mapped_column(Text, nullable=False)
    is_strict: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    playbook: Mapped[PlaybookModel] = relationship("PlaybookModel", back_populates="rules")


class PlaybookObjectionModel(PlaybookBase):
    """SQLAlchemy ORM Model mapping 'playbook_objections' table."""

    __tablename__ = "playbook_objections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    playbook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger_phrase: Mapped[str] = mapped_column(Text, nullable=False)
    objection_category: Mapped[str] = mapped_column(String(100), nullable=False, default="GENERAL")
    response_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_response: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    playbook: Mapped[PlaybookModel] = relationship("PlaybookModel", back_populates="objections")


class PlaybookExampleModel(PlaybookBase):
    """SQLAlchemy ORM Model mapping 'playbook_examples' table."""

    __tablename__ = "playbook_examples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    playbook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scenario: Mapped[str] = mapped_column(Text, nullable=False)
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    ideal_response: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    playbook: Mapped[PlaybookModel] = relationship("PlaybookModel", back_populates="examples")


class PlaybookTransitionModel(PlaybookBase):
    """SQLAlchemy ORM Model mapping 'playbook_transitions' table."""

    __tablename__ = "playbook_transitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    playbook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_stage_id: Mapped[str] = mapped_column(String(36), nullable=False)
    to_stage_id: Mapped[str] = mapped_column(String(36), nullable=False)
    condition: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    playbook: Mapped[PlaybookModel] = relationship("PlaybookModel", back_populates="transitions")
