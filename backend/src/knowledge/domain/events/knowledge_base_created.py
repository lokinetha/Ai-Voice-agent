"""
KnowledgeBaseCreated Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class KnowledgeBaseCreated(DomainEvent):
    """Domain Event published when a KnowledgeBase aggregate is created."""

    kb_id: str = ""
    workspace_id: str = ""
    name: str = ""
