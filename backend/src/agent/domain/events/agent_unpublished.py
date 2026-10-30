"""
AgentUnpublished Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class AgentUnpublished(DomainEvent):
    """Domain Event published when an Agent is paused or unpublished."""

    agent_id: str = ""
    workspace_id: str = ""
    reason: str = ""
