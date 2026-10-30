"""
DocumentDeleted Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class DocumentDeleted(DomainEvent):
    """Domain Event published when a Document is removed from a KnowledgeBase."""

    kb_id: str = ""
    document_id: str = ""
