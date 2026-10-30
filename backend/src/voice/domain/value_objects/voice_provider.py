"""
VoiceProvider Value Object.

Identifies external STT, TTS, or Telephony provider configurations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class VoiceProvider(ValueObject):
    """Immutable provider configuration reference.

    Attributes:
        provider_name: Provider identifier (e.g. "fake_stt", "fake_tts", "sip_gateway").
        config: Provider-specific configuration dictionary.
    """

    provider_name: str = "generic_voice_provider"
    config: dict[str, Any] = field(default_factory=dict)

    def _validate(self) -> None:
        if not self.provider_name or not self.provider_name.strip():
            raise ValueError("provider_name cannot be empty")
