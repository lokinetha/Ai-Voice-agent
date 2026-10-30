"""
AgentArchived Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class AgentArchived(DomainEvent):
    """Domain Event published when an Agent aggregate is archived."""

    agent_id: str = ""
    workspace_id: str = ""
