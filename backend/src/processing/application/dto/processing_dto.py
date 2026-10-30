"""
Processing Data Transfer Objects (DTOs) for Application Layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ChunkingStrategyDTO:
    """DTO representing ChunkingStrategy parameters."""

    strategy_type: str
    chunk_size: int
    chunk_overlap: int


@dataclass(frozen=True)
class EmbeddingStrategyDTO:
    """DTO representing EmbeddingStrategy parameters."""

    model_name: str
    dimension: int


@dataclass(frozen=True)
class ProcessingResultDTO:
    """DTO representing ProcessingResult outcome."""

    output_count: int
    execution_time_seconds: float
    metrics: dict[str, float]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ProcessingTaskDTO:
    """DTO representing a ProcessingTask step."""

    id: str
    task_type: str
    order: int
    status: str
    result: ProcessingResultDTO | None = None
    error_message: str = ""


@dataclass(frozen=True)
class ProcessingJobDTO:
    """DTO representing a ProcessingJob aggregate root."""

    id: str
    workspace_id: str
    document_id: str
    status: str
    chunking_strategy: ChunkingStrategyDTO
    embedding_strategy: EmbeddingStrategyDTO
    tasks: tuple[ProcessingTaskDTO, ...] = field(default_factory=tuple)
    chunk_references: tuple[str, ...] = field(default_factory=tuple)
    vector_references: tuple[str, ...] = field(default_factory=tuple)
    error_message: str = ""
    version: int = 1
    created_at: datetime | None = None
