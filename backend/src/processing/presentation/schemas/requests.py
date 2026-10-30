"""
Pydantic Request Schemas for Processing Presentation Layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProcessDocumentRequest(BaseModel):
    """HTTP Request schema for executing document processing pipeline."""

    workspace_id: str = Field(..., description="Workspace ID")
    document_id: str = Field(..., description="Document ID")
    storage_bucket: str = Field(..., description="Storage bucket name")
    storage_key: str = Field(..., description="Storage object key")
    file_type: str = Field(..., description="File extension/mime type")
    chunk_size: int = Field(default=500, description="Target chunk size in characters")
    chunk_overlap: int = Field(default=50, description="Chunk overlap in characters")
    embedding_model: str = Field(default="standard-text-embedding", description="Embedding model name")


class ChunkDocumentRequest(BaseModel):
    """HTTP Request schema for chunking text."""

    text: str = Field(..., description="Text content to segment into chunks")
    chunk_size: int = Field(default=500, description="Chunk size in characters")
    chunk_overlap: int = Field(default=50, description="Overlap in characters")
    strategy_type: str = Field(default="FIXED_SIZE", description="Strategy type")


class GenerateEmbeddingsRequest(BaseModel):
    """HTTP Request schema for generating vector embeddings."""

    texts: list[str] = Field(..., description="List of text strings to embed")
    model_name: str = Field(default="standard-text-embedding", description="Embedding model name")
    dimension: int = Field(default=768, description="Target vector dimension")


class AnalyzeConversationRequest(BaseModel):
    """HTTP Request schema for analyzing a completed conversation."""

    workspace_id: str = Field(..., description="Workspace ID")
    conversation_id: str = Field(..., description="Conversation ID")


class DetectBehaviorPatternsRequest(BaseModel):
    """HTTP Request schema for detecting patterns in message turns."""

    messages: list[dict[str, str]] = Field(..., description="List of message dicts with role and content")
    conversation_id: str = Field(default="", description="Optional conversation ID reference")
