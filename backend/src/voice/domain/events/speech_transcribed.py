"""
SpeechTranscribed Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class SpeechTranscribed(DomainEvent):
    """Domain Event published when user audio is transcribed to text."""

    session_id: str = ""
    turn_id: str = ""
    transcript: str = ""
    confidence: float = 1.0
