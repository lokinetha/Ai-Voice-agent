"""
AnalysisCompleted Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class AnalysisCompleted(DomainEvent):
    """Domain Event published when a ConversationAnalysis job completes successfully."""

    analysis_id: str = ""
    conversation_id: str = ""
    signals_count: int = 0
    patterns_count: int = 0
