"""
KnowledgeBaseReindexed Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class KnowledgeBaseReindexed(DomainEvent):
    """Domain Event published when a KnowledgeBase reindexing is initiated."""

    kb_id: str = ""
    document_count: int = 0
    total_chunks: int = 0
