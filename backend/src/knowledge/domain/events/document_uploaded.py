"""
DocumentUploaded Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class DocumentUploaded(DomainEvent):
    """Domain Event published when a Document is added to a KnowledgeBase."""

    kb_id: str = ""
    document_id: str = ""
    file_name: str = ""
    size_bytes: int = 0
