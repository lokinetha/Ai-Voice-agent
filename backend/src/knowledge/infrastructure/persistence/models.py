"""
SQLAlchemy 2.x Persistence Models for Knowledge Bounded Context.
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


class KnowledgeBaseBase(DeclarativeBase):
    """Declarative Base for Knowledge models."""

    pass


class KnowledgeBaseModel(KnowledgeBaseBase):
    """SQLAlchemy ORM Model mapping 'knowledge_bases' table."""

    __tablename__ = "knowledge_bases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")

    # Retrieval policy fields
    top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    similarity_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False, default="hybrid")
    reranking_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    documents: Mapped[list[DocumentModel]] = relationship(
        "DocumentModel", back_populates="knowledge_base", cascade="all, delete-orphan", lazy="selectin"
    )


class DocumentModel(KnowledgeBaseBase):
    """SQLAlchemy ORM Model mapping 'knowledge_documents' table."""

    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kb_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")

    # Embedded metadata
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/pdf")
    tags_json: Mapped[dict[str, Any]] = mapped_column("tags", JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    knowledge_base: Mapped[KnowledgeBaseModel] = relationship("KnowledgeBaseModel", back_populates="documents")
    chunks: Mapped[list[ChunkModel]] = relationship(
        "ChunkModel", back_populates="document", cascade="all, delete-orphan", lazy="selectin"
    )


class ChunkModel(KnowledgeBaseBase):
    """SQLAlchemy ORM Model mapping 'knowledge_chunks' table."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    document: Mapped[DocumentModel] = relationship("DocumentModel", back_populates="chunks")
