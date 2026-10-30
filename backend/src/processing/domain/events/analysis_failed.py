"""
AnalysisFailed Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class AnalysisFailed(DomainEvent):
    """Domain Event published when a ConversationAnalysis job fails."""

    analysis_id: str = ""
    conversation_id: str = ""
    error_message: str = ""
