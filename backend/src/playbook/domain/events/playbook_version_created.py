"""
PlaybookVersionCreated Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class PlaybookVersionCreated(DomainEvent):
    """Domain Event published when a new immutable version of a Playbook is created."""

    playbook_id: str = ""
    version_id: str = ""
    version_number: int = 1
