"""
AnalysisStarted Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class AnalysisStarted(DomainEvent):
    """Domain Event published when a ConversationAnalysis job starts."""

    analysis_id: str = ""
    conversation_id: str = ""
    workspace_id: str = ""
