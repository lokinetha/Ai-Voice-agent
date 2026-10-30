"""
VoiceSessionStarted Domain Event.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.domain_event import DomainEvent


@dataclass(frozen=True)
class VoiceSessionStarted(DomainEvent):
    """Domain Event published when a VoiceSession is started."""

    session_id: str = ""
    workspace_id: str = ""
    agent_id: str = ""
    conversation_id: str = ""
