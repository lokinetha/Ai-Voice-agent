"""
AgentVoiceConfig Value Object for Agent Bounded Context.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject
from shared.kernel.value_objects import Language


@dataclass(frozen=True)
class AgentVoiceConfig(ValueObject):
    """AgentVoiceConfig Value Object storing TTS provider parameters."""

    tts_provider: str
    voice_id: str
    speed: float = 1.0
    pitch: float = 1.0
    language: Language = Language("en-US")

    def _validate(self) -> None:
        if not self.tts_provider or not isinstance(self.tts_provider, str):
            raise ValueError("tts_provider cannot be empty")
        if not self.voice_id or not isinstance(self.voice_id, str):
            raise ValueError("voice_id cannot be empty")
        if not 0.5 <= self.speed <= 2.0:
            raise ValueError(f"speed must be between 0.5 and 2.0, got: {self.speed}")
        if not 0.5 <= self.pitch <= 2.0:
            raise ValueError(f"pitch must be between 0.5 and 2.0, got: {self.pitch}")

    @classmethod
    def default(cls) -> AgentVoiceConfig:
        return cls(
            tts_provider="elevenlabs",
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel default voice
            speed=1.0,
            pitch=1.0,
            language=Language("en-US"),
        )
