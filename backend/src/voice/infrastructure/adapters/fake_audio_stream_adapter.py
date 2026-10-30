"""
FakeAudioStreamAdapter implementing AudioStreamPort.

Provider-independent in-memory streaming audio channel adapter.
"""

from __future__ import annotations

from collections import deque

from voice.domain.ports.audio_stream_port import AudioStreamPort
from voice.domain.value_objects.audio_chunk import AudioChunk


class FakeAudioStreamAdapter(AudioStreamPort):
    """In-memory streaming audio channel adapter."""

    def __init__(self) -> None:
        self.channels: dict[str, deque[AudioChunk]] = {}

    async def send_audio_chunk(self, stream_id: str, chunk: AudioChunk) -> bool:
        """Transmit chunk to stream channel queue."""
        if stream_id not in self.channels:
            self.channels[stream_id] = deque()
        self.channels[stream_id].append(chunk)
        return True

    async def receive_audio_chunk(self, stream_id: str) -> AudioChunk | None:
        """Pop chunk from stream channel queue if available."""
        if stream_id in self.channels and self.channels[stream_id]:
            return self.channels[stream_id].popleft()
        return None
