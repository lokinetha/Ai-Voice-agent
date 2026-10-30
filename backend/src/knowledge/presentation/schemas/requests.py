"""
Pydantic Request Schemas for Knowledge Presentation Layer.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateKnowledgeBaseRequest(BaseModel):
    """HTTP Request schema for creating a new KnowledgeBase."""

    workspace_id: str = Field(..., description="Owning Workspace ID", examples=["ws-100"])
    name: str = Field(..., description="KnowledgeBase name", examples=["Sales Product SOPs"])
    description: str = Field(default="", description="Description of knowledge base content")
    top_k: int = Field(default=5, ge=1, le=100, description="Top-K vector results retrieval count")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    strategy: str = Field(default="hybrid", description="Retrieval strategy (dense, sparse, hybrid)")


class UploadDocumentRequest(BaseModel):
    """HTTP Request schema for registering document metadata in KnowledgeBase."""

    file_name: str = Field(..., description="Original filename", examples=["SOP_Handling_Objections.pdf"])
    file_type: str = Field(..., description="File extension", examples=["pdf"])
    size_bytes: int = Field(..., ge=0, description="File size in bytes", examples=[1048576])
    source_url: str | None = Field(default=None, description="Optional original URL")
    tags: dict[str, Any] | None = Field(default=None, description="Optional key-value metadata tags")


class SearchMetadataRequest(BaseModel):
    """HTTP Request schema for searching documents by metadata tags."""

    file_type: str | None = Field(default=None, description="Filter by file extension")
    tag_key: str | None = Field(default=None, description="Filter tag key")
    tag_value: Any | None = Field(default=None, description="Filter tag value")
