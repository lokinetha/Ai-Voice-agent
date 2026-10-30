"""
PlaybookPublished Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class PlaybookPublished(DomainEvent):
    """Domain Event published when a Playbook is published."""

    playbook_id: str = ""
    version_number: int = 1
