"""
PromptCompiled Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class PromptCompiled(DomainEvent):
    """Domain Event published when a Prompt is compiled from a Playbook."""

    prompt_id: str = ""
    source_playbook_id: str = ""
    source_playbook_version: int = 1
    checksum: str = ""
