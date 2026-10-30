"""
SpeechSynthesized Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class SpeechSynthesized(DomainEvent):
    """Domain Event published when agent text is synthesized to audio."""

    session_id: str = ""
    turn_id: str = ""
    audio_bytes_length: int = 0
