"""
ProcessingStarted Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class ProcessingStarted(DomainEvent):
    """Domain Event published when a ProcessingJob starts."""

    job_id: str = ""
    document_id: str = ""
    workspace_id: str = ""
