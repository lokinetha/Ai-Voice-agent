"""
PlaybookCreated Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class PlaybookCreated(DomainEvent):
    """Domain Event published when a new Playbook is created."""

    playbook_id: str = ""
    workspace_id: str = ""
    name: str = ""
