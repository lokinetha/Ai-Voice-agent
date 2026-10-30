"""
AudioStreamPort Interface for Voice Bounded Context.

Abstract port for managing transient streaming audio channels.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from voice.domain.value_objects.audio_chunk import AudioChunk


class AudioStreamPort(ABC):
    """Abstract port for low-level audio stream chunk transport."""

    @abstractmethod
    async def send_audio_chunk(self, stream_id: str, chunk: AudioChunk) -> bool:
        """Transmit audio chunk to stream channel.

        Args:
            stream_id: Target stream identifier.
            chunk: AudioChunk payload.

        Returns:
            True if chunk was transmitted successfully.
        """
        ...

    @abstractmethod
    async def receive_audio_chunk(self, stream_id: str) -> AudioChunk | None:
        """Receive next audio chunk from stream channel.

        Args:
            stream_id: Target stream identifier.

        Returns:
            AudioChunk if available, else None.
        """
        ...
