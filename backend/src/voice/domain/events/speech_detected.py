"""
SpeechDetected Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class SpeechDetected(DomainEvent):
    """Domain Event published when user speech is detected in the audio stream."""

    session_id: str = ""
    turn_id: str = ""
