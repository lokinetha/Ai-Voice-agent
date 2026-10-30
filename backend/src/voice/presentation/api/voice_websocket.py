"""
WebSocket Endpoint Abstraction for Voice Bounded Context.

Translates real-time audio WebSocket messages into ProcessAudioChunkCommand dispatches.
Rule enforced: No business logic in WebSocket controllers. Delegates strictly to application handlers.
"""

from __future__ import annotations

from typing import Any

from voice.application.commands.process_audio_chunk import (
    ProcessAudioChunkCommand,
    ProcessAudioChunkHandler,
)


class VoiceWebSocketHandler:
    """Thin WebSocket handler delegating real-time audio frames to CQRS handlers."""

    def __init__(self, process_chunk_handler: ProcessAudioChunkHandler) -> None:
        self._handler = process_chunk_handler

    async def handle_audio_frame(
        self, session_id: str, payload_bytes: bytes, sequence_number: int = 0, is_final: bool = False
    ) -> dict[str, Any]:
        """Handle incoming binary audio frame from WebSocket connection.

        Args:
            session_id: Target VoiceSession ID.
            payload_bytes: Binary audio bytes.
            sequence_number: Frame index.
            is_final: True if end of speech turn.

        Returns:
            Dictionary response status for WebSocket client.
        """
        cmd = ProcessAudioChunkCommand(
            session_id=session_id,
            audio_bytes=payload_bytes,
            sequence_number=sequence_number,
            is_final=is_final,
        )
        res = await self._handler.handle(cmd)

        if res.is_failure:
            return {"status": "error", "error": res.error.message}

        return {
            "status": "ok",
            "session_id": res.value.id,
            "turn_count": len(res.value.turns),
        }
