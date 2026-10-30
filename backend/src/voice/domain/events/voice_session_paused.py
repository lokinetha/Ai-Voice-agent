"""
VoiceSessionPaused Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class VoiceSessionPaused(DomainEvent):
    """Domain Event published when a VoiceSession is paused."""

    session_id: str = ""
