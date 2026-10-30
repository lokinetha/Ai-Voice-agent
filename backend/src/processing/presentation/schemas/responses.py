"""
Pydantic Response Schemas for Processing Presentation Layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChunkingStrategyResponse(BaseModel):
    strategy_type: str
    chunk_size: int
    chunk_overlap: int


class EmbeddingStrategyResponse(BaseModel):
    model_name: str
    dimension: int


class ProcessingResultResponse(BaseModel):
    output_count: int
    execution_time_seconds: float
    metrics: dict[str, float]
    metadata: dict[str, Any]


class ProcessingTaskResponse(BaseModel):
    id: str
    task_type: str
    order: int
    status: str
    result: ProcessingResultResponse | None = None
    error_message: str = ""


class ProcessingJobResponse(BaseModel):
    """HTTP Response schema representing a ProcessingJob aggregate."""

    id: str = Field(..., description="Job ID")
    workspace_id: str = Field(..., description="Workspace ID")
    document_id: str = Field(..., description="Document ID")
    status: str = Field(..., description="Status (PENDING, RUNNING, COMPLETED, FAILED)")
    chunking_strategy: ChunkingStrategyResponse
    embedding_strategy: EmbeddingStrategyResponse
    tasks: list[ProcessingTaskResponse] = Field(default_factory=list)
    chunk_references: list[str] = Field(default_factory=list)
    vector_references: list[str] = Field(default_factory=list)
    error_message: str = Field(default="", description="Error message if failed")
    version: int = Field(..., description="Aggregate version")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")


class ChunkDocumentResponse(BaseModel):
    chunks: list[str] = Field(..., description="List of generated text chunks")


class GenerateEmbeddingsResponse(BaseModel):
    vectors: list[list[float]] = Field(..., description="List of generated embedding vectors")


class BehavioralSignalResponse(BaseModel):
    id: str
    category: str
    signal_type: str
    description: str
    confidence: float
    source_message_id: str
    evidence_text: str


class ConversationPatternResponse(BaseModel):
    id: str
    pattern_name: str
    category: str
    description: str
    frequency: int
    confidence: float
    sample_signal_ids: list[str] = Field(default_factory=list)
    conversation_references: list[str] = Field(default_factory=list)


class AnalysisResultResponse(BaseModel):
    signals_count: int
    patterns_count: int
    execution_time_seconds: float
    summary: str
    metadata: dict[str, Any]


class ConversationAnalysisResponse(BaseModel):
    """HTTP Response schema representing a ConversationAnalysis aggregate."""

    id: str = Field(..., description="Analysis ID")
    workspace_id: str = Field(..., description="Workspace ID")
    conversation_id: str = Field(..., description="Conversation ID")
    status: str = Field(..., description="Status (PENDING, IN_PROGRESS, COMPLETED, FAILED)")
    signals: list[BehavioralSignalResponse] = Field(default_factory=list)
    patterns: list[ConversationPatternResponse] = Field(default_factory=list)
    result: AnalysisResultResponse | None = None
    error_message: str = Field(default="", description="Error message if failed")
    version: int = Field(..., description="Aggregate version")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
