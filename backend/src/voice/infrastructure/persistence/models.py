"""
SQLAlchemy 2.x Persistence Models for Voice Bounded Context.
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


class VoiceBase(DeclarativeBase):
    """Declarative Base for Voice models."""

    pass


class VoiceSessionModel(VoiceBase):
    """SQLAlchemy ORM Model mapping 'voice_sessions' table."""

    __tablename__ = "voice_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="IDLE")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")

    stt_provider_json: Mapped[dict[str, Any] | None] = mapped_column("stt_provider", JSON, nullable=True)
    tts_provider_json: Mapped[dict[str, Any] | None] = mapped_column("tts_provider", JSON, nullable=True)
    telephony_provider_json: Mapped[dict[str, Any] | None] = mapped_column("telephony_provider", JSON, nullable=True)
    metrics_json: Mapped[dict[str, Any] | None] = mapped_column("metrics", JSON, nullable=True)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    participants: Mapped[list[VoiceParticipantModel]] = relationship(
        "VoiceParticipantModel",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    streams: Mapped[list[AudioStreamModel]] = relationship(
        "AudioStreamModel",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    turns: Mapped[list[VoiceTurnModel]] = relationship(
        "VoiceTurnModel",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="VoiceTurnModel.turn_number",
    )


class VoiceParticipantModel(VoiceBase):
    """SQLAlchemy ORM Model mapping 'voice_participants' table."""

    __tablename__ = "voice_participants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("voice_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped[VoiceSessionModel] = relationship("VoiceSessionModel", back_populates="participants")


class AudioStreamModel(VoiceBase):
    """SQLAlchemy ORM Model mapping 'audio_streams' table."""

    __tablename__ = "audio_streams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("voice_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stream_type: Mapped[str] = mapped_column(String(50), nullable=False)
    audio_format_json: Mapped[dict[str, Any] | None] = mapped_column("audio_format", JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    chunks_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_bytes_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped[VoiceSessionModel] = relationship("VoiceSessionModel", back_populates="streams")


class VoiceTurnModel(VoiceBase):
    """SQLAlchemy ORM Model mapping 'voice_turns' table."""

    __tablename__ = "voice_turns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("voice_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    speaker_role: Mapped[str] = mapped_column(String(50), nullable=False)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    transcript: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    agent_response_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    audio_synthesized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped[VoiceSessionModel] = relationship("VoiceSessionModel", back_populates="turns")
