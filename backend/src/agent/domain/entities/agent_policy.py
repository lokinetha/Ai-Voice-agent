"""
AgentPolicy Entity for Agent Bounded Context.

Represents a safety, compliance, or behavioral guardrail policy enforced on an Agent.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp


class AgentPolicy(Entity):
    """AgentPolicy Entity child of Agent aggregate root."""

    def __init__(
        self,
        id: EntityId,
        policy_type: str,
        rule: str,
        violation_action: str = "transfer_to_human",
        enforced: bool = True,
        priority: int = 1,
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not policy_type or not isinstance(policy_type, str):
            raise ValueError("AgentPolicy policy_type cannot be empty")
        if not rule or not isinstance(rule, str) or not rule.strip():
            raise ValueError("AgentPolicy rule cannot be empty")

        self._policy_type = policy_type
        self._rule = rule.strip()
        self._violation_action = violation_action
        self._enforced = enforced
        self._priority = priority

    @property
    def policy_type(self) -> str:
        return self._policy_type

    @property
    def rule(self) -> str:
        return self._rule

    @property
    def violation_action(self) -> str:
        return self._violation_action

    @property
    def enforced(self) -> bool:
        return self._enforced

    @property
    def priority(self) -> int:
        return self._priority

    @classmethod
    def default_fallback(cls) -> AgentPolicy:
        """Construct default fallback policy."""
        return cls(
            id=EntityId(),
            policy_type="FALLBACK",
            rule="When uncertain or when customer requests human, transfer call",
            violation_action="transfer_to_human",
            enforced=True,
            priority=100,
        )
