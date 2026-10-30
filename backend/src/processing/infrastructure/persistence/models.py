"""
SQLAlchemy 2.x Persistence Models for Processing Bounded Context.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class ProcessingBase(DeclarativeBase):
    """Declarative Base for Processing models."""

    pass


class ProcessingJobModel(ProcessingBase):
    """SQLAlchemy ORM Model mapping 'processing_jobs' table."""

    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")

    chunking_strategy_json: Mapped[dict[str, Any] | None] = mapped_column(
        "chunking_strategy", JSON, nullable=True
    )
    embedding_strategy_json: Mapped[dict[str, Any] | None] = mapped_column(
        "embedding_strategy", JSON, nullable=True
    )

    chunk_references_json: Mapped[list[str] | None] = mapped_column(
        "chunk_references", JSON, nullable=True
    )
    vector_references_json: Mapped[list[str] | None] = mapped_column(
        "vector_references", JSON, nullable=True
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    tasks: Mapped[list[ProcessingTaskModel]] = relationship(
        "ProcessingTaskModel",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProcessingTaskModel.order",
    )


class ProcessingTaskModel(ProcessingBase):
    """SQLAlchemy ORM Model mapping 'processing_tasks' table."""

    __tablename__ = "processing_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result_json: Mapped[dict[str, Any] | None] = mapped_column("result", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    job: Mapped[ProcessingJobModel] = relationship("ProcessingJobModel", back_populates="tasks")


class ConversationAnalysisModel(ProcessingBase):
    """SQLAlchemy ORM Model mapping 'conversation_analyses' table."""

    __tablename__ = "conversation_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result_json: Mapped[dict[str, Any] | None] = mapped_column("result", JSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    signals: Mapped[list[BehavioralSignalModel]] = relationship(
        "BehavioralSignalModel",
        back_populates="analysis",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    patterns: Mapped[list[ConversationPatternModel]] = relationship(
        "ConversationPatternModel",
        back_populates="analysis",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class BehavioralSignalModel(ProcessingBase):
    """SQLAlchemy ORM Model mapping 'behavioral_signals' table."""

    __tablename__ = "behavioral_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversation_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    source_message_id: Mapped[str] = mapped_column(String(36), nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    analysis: Mapped[ConversationAnalysisModel] = relationship("ConversationAnalysisModel", back_populates="signals")


class ConversationPatternModel(ProcessingBase):
    """SQLAlchemy ORM Model mapping 'conversation_patterns' table."""

    __tablename__ = "conversation_patterns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversation_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pattern_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    sample_signal_ids_json: Mapped[list[str] | None] = mapped_column("sample_signal_ids", JSON, nullable=True)
    conversation_references_json: Mapped[list[str] | None] = mapped_column("conversation_references", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    analysis: Mapped[ConversationAnalysisModel] = relationship("ConversationAnalysisModel", back_populates="patterns")
