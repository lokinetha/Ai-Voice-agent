"""
AgentCloned Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class AgentCloned(DomainEvent):
    """Domain Event published when an Agent aggregate is cloned."""

    source_agent_id: str = ""
    new_agent_id: str = ""
    workspace_id: str = ""
    new_agent_name: str = ""
