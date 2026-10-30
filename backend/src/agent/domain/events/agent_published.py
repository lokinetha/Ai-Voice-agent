"""
AgentPublished Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class AgentPublished(DomainEvent):
    """Domain Event published when an Agent state is set to PUBLISHED."""

    agent_id: str = ""
    workspace_id: str = ""
    playbook_id: str = ""
    prompt_id: str = ""
    version: int = 1
