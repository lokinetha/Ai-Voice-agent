"""
SQLAlchemy 2.x Persistence Models for Conversation Bounded Context.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class ConversationBase(DeclarativeBase):
    """Declarative Base for Conversation models."""

    pass


class ConversationModel(ConversationBase):
    """SQLAlchemy ORM Model mapping 'conversations' table."""

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en-US")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")

    # Metrics
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_messages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    agent_messages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    customer_messages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Summary
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_topics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    summary_sentiment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary_actions: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    participants: Mapped[list[ParticipantModel]] = relationship(
        "ParticipantModel", back_populates="conversation", cascade="all, delete-orphan", lazy="selectin"
    )
    messages: Mapped[list[MessageModel]] = relationship(
        "MessageModel", back_populates="conversation", cascade="all, delete-orphan", lazy="selectin",
        order_by="MessageModel.sequence_number",
    )


class ParticipantModel(ConversationBase):
    """SQLAlchemy ORM Model mapping 'conversation_participants' table."""

    __tablename__ = "conversation_participants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    conversation: Mapped[ConversationModel] = relationship("ConversationModel", back_populates="participants")


class MessageModel(ConversationBase):
    """SQLAlchemy ORM Model mapping 'conversation_messages' table."""

    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    conversation: Mapped[ConversationModel] = relationship("ConversationModel", back_populates="messages")
