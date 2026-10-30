"""
ProcessingCompleted Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class ProcessingCompleted(DomainEvent):
    """Domain Event published when a ProcessingJob completes successfully."""

    job_id: str = ""
    document_id: str = ""
    chunk_count: int = 0
    vector_count: int = 0
