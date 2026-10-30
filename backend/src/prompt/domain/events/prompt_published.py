"""
PromptPublished Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class PromptPublished(DomainEvent):
    """Domain Event published when a Prompt is published to production."""

    prompt_id: str = ""
    version_number: int = 1
