"""
AgentCreated Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class AgentCreated(DomainEvent):
    """Domain Event published when an Agent aggregate is created.

    Attributes:
        agent_id: AgentId string.
        workspace_id: WorkspaceId string.
        agent_name: Name of created agent.
        agent_type: Category/Type string of agent.
    """

    agent_id: str = ""
    workspace_id: str = ""
    agent_name: str = ""
    agent_type: str = ""
