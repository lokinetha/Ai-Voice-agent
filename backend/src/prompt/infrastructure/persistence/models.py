"""
SQLAlchemy 2.x Persistence Models for Prompt Bounded Context.
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


class PromptBase(DeclarativeBase):
    """Declarative Base for Prompt models."""

    pass


class PromptModel(PromptBase):
    """SQLAlchemy ORM Model mapping 'prompts' table."""

    __tablename__ = "prompts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    compiled_prompt_text: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Version Info
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    version_label: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    version_changelog: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Provenance Metadata & Template
    compilation_metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "compilation_metadata", JSON, nullable=True
    )
    template_json: Mapped[dict[str, Any] | None] = mapped_column("template", JSON, nullable=True)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sections: Mapped[list[PromptSectionModel]] = relationship(
        "PromptSectionModel",
        back_populates="prompt",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PromptSectionModel.order",
    )
    constraints: Mapped[list[PromptConstraintModel]] = relationship(
        "PromptConstraintModel",
        back_populates="prompt",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    examples: Mapped[list[PromptExampleModel]] = relationship(
        "PromptExampleModel",
        back_populates="prompt",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class PromptSectionModel(PromptBase):
    """SQLAlchemy ORM Model mapping 'prompt_sections' table."""

    __tablename__ = "prompt_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    prompt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    prompt: Mapped[PromptModel] = relationship("PromptModel", back_populates="sections")
    instructions: Mapped[list[PromptInstructionModel]] = relationship(
        "PromptInstructionModel",
        back_populates="section",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PromptInstructionModel.order",
    )


class PromptInstructionModel(PromptBase):
    """SQLAlchemy ORM Model mapping 'prompt_instructions' table."""

    __tablename__ = "prompt_instructions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    section_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("prompt_sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    section: Mapped[PromptSectionModel] = relationship("PromptSectionModel", back_populates="instructions")


class PromptConstraintModel(PromptBase):
    """SQLAlchemy ORM Model mapping 'prompt_constraints' table."""

    __tablename__ = "prompt_constraints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    prompt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    constraint_type: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    prompt: Mapped[PromptModel] = relationship("PromptModel", back_populates="constraints")


class PromptExampleModel(PromptBase):
    """SQLAlchemy ORM Model mapping 'prompt_examples' table."""

    __tablename__ = "prompt_examples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    prompt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    ideal_response: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    prompt: Mapped[PromptModel] = relationship("PromptModel", back_populates="examples")
