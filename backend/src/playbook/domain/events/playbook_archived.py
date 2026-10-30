"""
PlaybookArchived Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class PlaybookArchived(DomainEvent):
    """Domain Event published when a Playbook is archived."""

    playbook_id: str = ""
    reason: str = ""
