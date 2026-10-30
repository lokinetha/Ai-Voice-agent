"""
BehavioralPatternDetected Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class BehavioralPatternDetected(DomainEvent):
    """Domain Event published when a significant behavioral pattern is detected."""

    analysis_id: str = ""
    pattern_name: str = ""
    category: str = ""
    confidence_score: float = 1.0
