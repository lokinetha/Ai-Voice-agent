"""
PromptArchived Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class PromptArchived(DomainEvent):
    """Domain Event published when a Prompt is archived."""

    prompt_id: str = ""
    reason: str = ""
