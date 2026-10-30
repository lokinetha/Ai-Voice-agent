"""
AudioStream Entity for Voice Bounded Context.

Manages state, format, and metadata of a real-time input/output audio stream.
Transient audio payload chunks are passed via AudioChunk VOs, not persisted directly as entities.
"""

from __future__ import annotations

from shared.kernel.entity import Entity
from shared.kernel.value_objects import EntityId, Timestamp

from voice.domain.value_objects.audio_format import AudioFormat


class AudioStream(Entity[EntityId]):
    """Entity representing an active inbound or outbound audio stream connection."""

    def __init__(
        self,
        id: EntityId,
        stream_type: str,
        audio_format: AudioFormat | None = None,
        is_active: bool = True,
        chunks_processed: int = 0,
        total_bytes_processed: int = 0,
        created_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at)

        if not stream_type or not stream_type.strip():
            raise ValueError("stream_type cannot be empty")

        self._stream_type = stream_type.strip().upper()  # INBOUND or OUTBOUND
        self._audio_format = audio_format or AudioFormat()
        self._is_active = is_active
        self._chunks_processed = chunks_processed
        self._total_bytes_processed = total_bytes_processed

    @property
    def stream_type(self) -> str:
        return self._stream_type

    @property
    def audio_format(self) -> AudioFormat:
        return self._audio_format

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def chunks_processed(self) -> int:
        return self._chunks_processed

    @property
    def total_bytes_processed(self) -> int:
        return self._total_bytes_processed

    def record_chunk(self, byte_count: int) -> None:
        """Record chunk reception in stream statistics."""
        if not self._is_active:
            raise ValueError("Cannot process chunk on inactive stream")
        self._chunks_processed += 1
        self._total_bytes_processed += byte_count

    def close(self) -> None:
        """Close stream."""
        self._is_active = False
