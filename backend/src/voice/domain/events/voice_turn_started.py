"""
VoiceTurnStarted Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class VoiceTurnStarted(DomainEvent):
    """Domain Event published when a new VoiceTurn starts."""

    session_id: str = ""
    turn_id: str = ""
    speaker_role: str = ""
