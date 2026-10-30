"""
VoiceSessionEnded Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class VoiceSessionEnded(DomainEvent):
    """Domain Event published when a VoiceSession is ended."""

    session_id: str = ""
    reason: str = ""
    total_turns: int = 0
