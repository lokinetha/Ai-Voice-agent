"""
CanAcceptAudioSpec Specification for Voice Bounded Context.
"""

from __future__ import annotations

from shared.kernel.specification import Specification

from voice.domain.entities.voice_session import VoiceSession


class CanAcceptAudioSpec(Specification[VoiceSession]):
    """Specification checking if a VoiceSession can accept incoming audio stream chunks."""

    def is_satisfied_by(self, candidate: VoiceSession) -> bool:
        if not candidate.status.is_active:
            return False
        # Check if there is at least one active inbound stream
        return any(s.is_active and s.stream_type == "INBOUND" for s in candidate.streams)
