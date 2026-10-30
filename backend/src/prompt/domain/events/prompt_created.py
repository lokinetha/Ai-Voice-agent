"""
PromptCreated Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class PromptCreated(DomainEvent):
    """Domain Event published when a Prompt is created."""

    prompt_id: str = ""
    workspace_id: str = ""
    name: str = ""
