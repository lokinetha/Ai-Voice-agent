"""
Pydantic Response Schemas for Knowledge Presentation Layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentMetadataResponse(BaseModel):
    file_type: str
    size_bytes: int
    source_url: str | None
    mime_type: str
    tags: dict[str, Any]


class RetrievalPolicyResponse(BaseModel):
    top_k: int
    similarity_threshold: float
    strategy: str
    reranking_enabled: bool


class ChunkResponse(BaseModel):
    id: str
    text_content: str
    sequence_index: int
    token_count: int
    embedding_id: str | None
    created_at: datetime


class DocumentResponse(BaseModel):
    id: str
    file_name: str
    status: str
    metadata: DocumentMetadataResponse
    chunk_count: int
    created_at: datetime
    chunks: list[ChunkResponse] = Field(default_factory=list)


class KnowledgeBaseResponse(BaseModel):
    """HTTP Response schema representing a KnowledgeBase aggregate."""

    id: str = Field(..., description="KnowledgeBase ID")
    workspace_id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="KnowledgeBase name")
    description: str = Field(..., description="Description")
    status: str = Field(..., description="Status (ACTIVE, INDEXING, etc.)")
    retrieval_policy: RetrievalPolicyResponse
    document_count: int = Field(..., description="Total documents in KnowledgeBase")
    total_chunks: int = Field(..., description="Total chunks across documents")
    version: int = Field(..., description="Optimistic concurrency version")
    created_at: datetime = Field(..., description="Creation timestamp")
    documents: list[DocumentResponse] = Field(default_factory=list)
