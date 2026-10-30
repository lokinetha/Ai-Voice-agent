"""
PlanValidationService Domain Service for Organization Bounded Context.

Validates operational resource usage against Organization subscription plan limits.
"""

from __future__ import annotations

from shared.kernel.domain_service import DomainService
from shared.kernel.result import Error, Result

from organization.domain.entities.organization import Organization


class PlanValidationService(DomainService):
    """Domain Service for validating tenant resource requests against plan quotas."""

    def validate_agent_creation(
        self, organization: Organization, current_agent_count: int
    ) -> Result[None]:
        """Validate whether a new agent can be created under current plan limits.

        Args:
            organization: Organization aggregate root.
            current_agent_count: Current count of agents in tenant.

        Returns:
            Result indicating success or LIMIT_EXCEEDED Error.
        """
        max_agents = organization.plan.max_agents
        if current_agent_count >= max_agents:
            return Result.fail(
                Error(
                    "LIMIT_EXCEEDED",
                    f"Agent quota reached for {organization.plan.tier.value} plan "
                    f"({current_agent_count}/{max_agents})",
                )
            )
        return Result.ok(None)

    def validate_document_ingestion(
        self, organization: Organization, current_doc_count: int
    ) -> Result[None]:
        """Validate whether a new knowledge document can be ingested under current plan limits."""
        max_docs = organization.plan.max_kb_documents
        if current_doc_count >= max_docs:
            return Result.fail(
                Error(
                    "LIMIT_EXCEEDED",
                    f"Knowledge Document quota reached for {organization.plan.tier.value} plan "
                    f"({current_doc_count}/{max_docs})",
                )
            )
        return Result.ok(None)
