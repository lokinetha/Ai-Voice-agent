"""
AudioFormat Value Object.

Defines parameters of an audio stream or chunk.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.value_object import ValueObject


@dataclass(frozen=True)
class AudioFormat(ValueObject):
    """Immutable audio stream format configuration.

    Attributes:
        sample_rate: Sample rate in Hz (e.g. 8000, 16000, 24000, 44100).
        channels: Channel count (1 for mono, 2 for stereo).
        encoding: Audio codec/encoding (e.g. "pcm_s16le", "mulaw", "alaw", "opus").
        container: Audio container format (e.g. "raw", "wav", "ogg").
    """

    sample_rate: int = 16000
    channels: int = 1
    encoding: str = "pcm_s16le"
    container: str = "raw"

    def _validate(self) -> None:
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if self.channels not in (1, 2):
            raise ValueError("channels must be 1 (mono) or 2 (stereo)")
        if not self.encoding or not self.encoding.strip():
            raise ValueError("encoding cannot be empty")
