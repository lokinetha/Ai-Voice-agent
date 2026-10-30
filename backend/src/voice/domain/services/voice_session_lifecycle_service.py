"""
VoiceSessionLifecycleService Domain Service for Voice Bounded Context.

Enforces business rules governing voice session lifecycle state transitions.
"""

from __future__ import annotations

from shared.kernel.domain_service import DomainService
from shared.kernel.result import Error, Result

from voice.domain.entities.voice_session import VoiceSession
from voice.domain.specifications.active_voice_session_spec import (
    ActiveVoiceSessionSpec,
)


class VoiceSessionLifecycleService(DomainService):
    """Domain Service managing VoiceSession lifecycle rules."""

    def __init__(self) -> None:
        self._active_spec = ActiveVoiceSessionSpec()

    def can_start_session(self, session: VoiceSession) -> Result[None]:
        """Verify session can transition to ACTIVE status."""
        if session.status.is_active:
            return Result.fail(Error("INVALID_STATE", "VoiceSession is already active"))
        if session.status.is_ended or session.status.is_failed:
            return Result.fail(Error("INVALID_STATE", "Cannot start a terminal session"))
        return Result.ok(None)

    def can_pause_session(self, session: VoiceSession) -> Result[None]:
        """Verify session can transition to PAUSED status."""
        if not self._active_spec.is_satisfied_by(session):
            return Result.fail(Error("INVALID_STATE", "Only active VoiceSessions can be paused"))
        return Result.ok(None)

    def can_end_session(self, session: VoiceSession) -> Result[None]:
        """Verify session can transition to ENDED status."""
        if session.status.is_ended or session.status.is_failed:
            return Result.fail(Error("INVALID_STATE", "VoiceSession is already terminal"))
        return Result.ok(None)
