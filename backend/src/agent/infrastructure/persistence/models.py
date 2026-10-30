"""
SQLAlchemy 2.x Persistence Models for Agent Bounded Context.
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


class AgentBase(DeclarativeBase):
    """Declarative base for Agent models."""



class AgentModel(AgentBase):
    """SQLAlchemy ORM Model mapping 'agents' table."""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="SALES")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")

    # References
    playbook_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    prompt_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Embedded configuration relationship models (1-to-1)
    voice_config: Mapped[AgentVoiceConfigModel] = relationship(
        "AgentVoiceConfigModel", back_populates="agent", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    runtime_config: Mapped[AgentRuntimeConfigModel] = relationship(
        "AgentRuntimeConfigModel", back_populates="agent", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    llm_config: Mapped[AgentLLMConfigModel] = relationship(
        "AgentLLMConfigModel", back_populates="agent", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    memory_config: Mapped[AgentMemoryConfigModel] = relationship(
        "AgentMemoryConfigModel", back_populates="agent", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )

    # Collections
    tools: Mapped[list[AgentToolModel]] = relationship(
        "AgentToolModel", back_populates="agent", cascade="all, delete-orphan", lazy="selectin"
    )
    policies: Mapped[list[AgentPolicyModel]] = relationship(
        "AgentPolicyModel", back_populates="agent", cascade="all, delete-orphan", lazy="selectin"
    )


class AgentVoiceConfigModel(AgentBase):
    __tablename__ = "agent_voice_configs"

    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True)
    tts_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="elevenlabs")
    voice_id: Mapped[str] = mapped_column(String(255), nullable=False)
    speed: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    pitch: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en-US")

    agent: Mapped[AgentModel] = relationship("AgentModel", back_populates="voice_config")


class AgentRuntimeConfigModel(AgentBase):
    __tablename__ = "agent_runtime_configs"

    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True)
    max_concurrent_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    session_timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=600)
    silence_threshold_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=800)
    barge_in_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    agent: Mapped[AgentModel] = relationship("AgentModel", back_populates="runtime_config")


class AgentLLMConfigModel(AgentBase):
    __tablename__ = "agent_llm_configs"

    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="gemini")
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="gemini-2.0-flash")
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    context_window: Mapped[int] = mapped_column(Integer, nullable=False, default=128000)

    agent: Mapped[AgentModel] = relationship("AgentModel", back_populates="llm_config")


class AgentMemoryConfigModel(AgentBase):
    __tablename__ = "agent_memory_configs"

    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True)
    short_term_window_size: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    long_term_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    long_term_strategy: Mapped[str] = mapped_column(String(50), nullable=False, default="vector_search")

    agent: Mapped[AgentModel] = relationship("AgentModel", back_populates="memory_config")


class AgentToolModel(AgentBase):
    __tablename__ = "agent_tools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tool_type: Mapped[str] = mapped_column(String(50), nullable=False)
    schema_json: Mapped[dict[str, Any]] = mapped_column("schema", JSON, nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column("config", JSON, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    agent: Mapped[AgentModel] = relationship("AgentModel", back_populates="tools")


class AgentPolicyModel(AgentBase):
    __tablename__ = "agent_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rule: Mapped[str] = mapped_column(Text, nullable=False)
    violation_action: Mapped[str] = mapped_column(String(100), nullable=False, default="transfer_to_human")
    enforced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    agent: Mapped[AgentModel] = relationship("AgentModel", back_populates="policies")
