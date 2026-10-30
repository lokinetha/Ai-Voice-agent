"""
PromptVersionCreated Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class PromptVersionCreated(DomainEvent):
    """Domain Event published when a new immutable version of a Prompt is created."""

    prompt_id: str = ""
    version_id: str = ""
    version_number: int = 1
