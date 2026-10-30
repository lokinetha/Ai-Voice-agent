"""
ActiveAgentSpec Specification for Agent Bounded Context.
"""

from __future__ import annotations

from shared.kernel.specification import Specification

from agent.domain.entities.agent import Agent
from agent.domain.value_objects.agent_status import AgentStatusType


class ActiveAgentSpec(Specification[Agent]):
    """Specification matching active (non-archived) Agents."""

    def is_satisfied_by(self, candidate: Agent) -> bool:
        return candidate.status.value != AgentStatusType.ARCHIVED
