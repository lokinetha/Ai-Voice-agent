"""
PlaybookUpdated Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class PlaybookUpdated(DomainEvent):
    """Domain Event published when a Playbook is updated."""

    playbook_id: str = ""
    name: str = ""
