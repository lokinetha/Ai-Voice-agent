"""
VoiceTurn Entity for Voice Bounded Context.

Represents a single turn in a VoiceSession (User speech or Agent speech turn).
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp

from voice.domain.value_objects.speech_confidence import SpeechConfidence


class VoiceTurn(Entity[EntityId]):
    """Entity representing a voice turn during a VoiceSession."""

    def __init__(
        self,
        id: EntityId,
        speaker_role: str,
        turn_number: int,
        transcript: str = "",
        confidence: SpeechConfidence | None = None,
        agent_response_text: str = "",
        audio_synthesized: bool = False,
        is_completed: bool = False,
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if turn_number < 1:
            raise ValueError("turn_number must be >= 1")

        self._speaker_role = speaker_role.strip().upper()
        self._turn_number = turn_number
        self._transcript = transcript.strip()
        self._confidence = confidence or SpeechConfidence(1.0)
        self._agent_response_text = agent_response_text.strip()
        self._audio_synthesized = audio_synthesized
        self._is_completed = is_completed

    @property
    def speaker_role(self) -> str:
        return self._speaker_role

    @property
    def turn_number(self) -> int:
        return self._turn_number

    @property
    def transcript(self) -> str:
        return self._transcript

    @property
    def confidence(self) -> SpeechConfidence:
        return self._confidence

    @property
    def agent_response_text(self) -> str:
        return self._agent_response_text

    @property
    def audio_synthesized(self) -> bool:
        return self._audio_synthesized

    @property
    def is_completed(self) -> bool:
        return self._is_completed

    def set_transcript(self, text: str, confidence: SpeechConfidence) -> None:
        """Update turn with transcribed text."""
        self._transcript = text.strip()
        self._confidence = confidence

    def set_agent_response(self, text: str) -> None:
        """Update turn with agent response text."""
        self._agent_response_text = text.strip()

    def mark_synthesized(self) -> None:
        """Mark TTS synthesis as completed for turn."""
        self._audio_synthesized = True

    def complete(self) -> None:
        """Complete the turn."""
        self._is_completed = True
