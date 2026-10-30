"""
PublishableAgentSpec Specification for Agent Bounded Context.
"""

from __future__ import annotations

from shared.kernel.specification import Specification

from agent.domain.entities.agent import Agent


class PublishableAgentSpec(Specification[Agent]):
    """Specification evaluating if an Agent is eligible for publishing."""

    def is_satisfied_by(self, candidate: Agent) -> bool:
        return (
            candidate.playbook_id is not None
            and bool(candidate.playbook_id.value)
            and candidate.prompt_id is not None
            and bool(candidate.prompt_id.value)
            and not candidate.status.is_archived
        )
