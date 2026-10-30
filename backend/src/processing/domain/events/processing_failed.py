"""
ProcessingFailed Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class ProcessingFailed(DomainEvent):
    """Domain Event published when a ProcessingJob fails."""

    job_id: str = ""
    document_id: str = ""
    error_message: str = ""
