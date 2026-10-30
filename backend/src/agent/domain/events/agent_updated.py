"""
AgentUpdated Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class AgentUpdated(DomainEvent):
    """Domain Event published when Agent configurations are updated."""

    agent_id: str = ""
    workspace_id: str = ""
    updated_fields: tuple[str, ...] = ()
