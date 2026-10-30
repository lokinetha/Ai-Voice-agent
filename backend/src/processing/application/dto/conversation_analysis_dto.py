"""
ConversationAnalysis Data Transfer Objects (DTOs).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class BehavioralSignalDTO:
    """DTO representing a detected BehavioralSignal."""

    id: str
    category: str
    signal_type: str
    description: str
    confidence: float
    source_message_id: str
    evidence_text: str


@dataclass(frozen=True)
class ConversationPatternDTO:
    """DTO representing a detected ConversationPattern."""

    id: str
    pattern_name: str
    category: str
    description: str
    frequency: int
    confidence: float
    sample_signal_ids: tuple[str, ...] = field(default_factory=tuple)
    conversation_references: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AnalysisResultDTO:
    """DTO representing AnalysisResult details."""

    signals_count: int
    patterns_count: int
    execution_time_seconds: float
    summary: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ConversationAnalysisDTO:
    """DTO representing ConversationAnalysis aggregate root."""

    id: str
    workspace_id: str
    conversation_id: str
    status: str
    signals: tuple[BehavioralSignalDTO, ...] = field(default_factory=tuple)
    patterns: tuple[ConversationPatternDTO, ...] = field(default_factory=tuple)
    result: AnalysisResultDTO | None = None
    error_message: str = ""
    version: int = 1
    created_at: datetime | None = None
