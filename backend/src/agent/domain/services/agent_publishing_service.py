"""
AgentPublishingService Domain Service for Agent Bounded Context.

Validates publishing preconditions and coordinates Agent publishing domain logic.
"""

from __future__ import annotations

from shared.kernel.domain_service import DomainService
from shared.kernel.result import Error, Result

from agent.domain.entities.agent import Agent
from agent.domain.specifications.publishable_agent_spec import PublishableAgentSpec


class AgentPublishingService(DomainService):
    """Domain Service verifying Agent publishing eligibility."""

    def __init__(self) -> None:
        self._spec = PublishableAgentSpec()

    def validate_and_publish(self, agent: Agent) -> Result[None]:
        """Validate all domain invariants and set Agent to published state.

        Args:
            agent: Agent aggregate root instance.

        Returns:
            Result indicating success or PRECONDITION_FAILED Error.
        """
        if not self._spec.is_satisfied_by(agent):
            if agent.playbook_id is None or not agent.playbook_id.value:
                return Result.fail(
                    Error("PRECONDITION_FAILED", "Cannot publish Agent without an active Playbook")
                )
            if agent.prompt_id is None or not agent.prompt_id.value:
                return Result.fail(
                    Error("PRECONDITION_FAILED", "Cannot publish Agent without an active Prompt")
                )
            if agent.status.is_archived:
                return Result.fail(
                    Error("INVALID_STATE", "Cannot publish an archived Agent")
                )

        return agent.publish()
