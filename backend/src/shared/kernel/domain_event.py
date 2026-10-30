"""
DomainEvent Base Implementation.

Defines immutable, serializable events published by Aggregate Roots upon state changes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    Attributes:
        event_id: Unique identifier for this specific event occurrence.
        occurred_at: UTC timestamp when the event occurred.
        tenant_id: Organization / Tenant isolation boundary.
        correlation_id: Correlation ID for distributed tracing across workflows.
        causation_id: Parent event ID that triggered this event.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    tenant_id: str = ""
    correlation_id: str = ""
    causation_id: str = ""

    @property
    def event_type(self) -> str:
        """Returns the qualified class name of the domain event."""
        return self.__class__.__qualname__
