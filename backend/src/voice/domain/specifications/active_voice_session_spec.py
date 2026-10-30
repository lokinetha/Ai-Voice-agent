"""
ActiveVoiceSessionSpec Specification for Voice Bounded Context.
"""

from __future__ import annotations

from shared.kernel.specification import Specification

from voice.domain.entities.voice_session import VoiceSession


class ActiveVoiceSessionSpec(Specification[VoiceSession]):
    """Specification verifying that a VoiceSession is currently active."""

    def is_satisfied_by(self, candidate: VoiceSession) -> bool:
        return candidate.status.is_active
