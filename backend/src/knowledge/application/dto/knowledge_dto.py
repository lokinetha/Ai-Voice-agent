"""
Knowledge Data Transfer Objects (DTOs) for Application Layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DocumentMetadataDTO:
    file_type: str
    size_bytes: int
    source_url: str | None
    mime_type: str
    tags: dict[str, Any]


@dataclass(frozen=True)
class RetrievalPolicyDTO:
    top_k: int
    similarity_threshold: float
    strategy: str
    reranking_enabled: bool


@dataclass(frozen=True)
class ChunkDTO:
    id: str
    text_content: str
    sequence_index: int
    token_count: int
    embedding_id: str | None
    created_at: datetime


@dataclass(frozen=True)
class DocumentDTO:
    id: str
    file_name: str
    status: str
    metadata: DocumentMetadataDTO
    chunk_count: int
    created_at: datetime
    chunks: tuple[ChunkDTO, ...] = ()


@dataclass(frozen=True)
class KnowledgeBaseDTO:
    id: str
    workspace_id: str
    name: str
    description: str
    status: str
    retrieval_policy: RetrievalPolicyDTO
    document_count: int
    total_chunks: int
    version: int
    created_at: datetime
    documents: tuple[DocumentDTO, ...] = ()
