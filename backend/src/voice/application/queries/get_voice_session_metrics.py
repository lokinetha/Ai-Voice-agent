"""
GetVoiceSessionMetrics Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import EntityId

from voice.application.dto.voice_dto import VoiceSessionMetricsDTO
from voice.domain.repositories.voice_session_repository import (
    VoiceSessionRepository,
)


@dataclass(frozen=True)
class GetVoiceSessionMetricsQuery(Query):
    """Query requesting operational metrics for a VoiceSession."""

    session_id: str


class GetVoiceSessionMetricsHandler(QueryHandler[GetVoiceSessionMetricsQuery, VoiceSessionMetricsDTO]):
    """Handler executing GetVoiceSessionMetricsQuery."""

    def __init__(self, session_repository: VoiceSessionRepository) -> None:
        self._repo = session_repository

    async def handle(self, query: GetVoiceSessionMetricsQuery) -> Result[VoiceSessionMetricsDTO]:
        """Execute GetVoiceSessionMetricsQuery."""
        if not query.session_id:
            return Result.fail(Error("VALIDATION_ERROR", "Session ID cannot be empty"))

        session = await self._repo.get_by_id(EntityId(query.session_id))
        if session is None:
            return Result.fail(Error("NOT_FOUND", f"VoiceSession '{query.session_id}' not found"))

        metrics_dto = VoiceSessionMetricsDTO(
            total_turns=session.metrics.total_turns,
            audio_duration_seconds=session.metrics.audio_duration_seconds,
            average_latency_ms=session.metrics.average_latency_ms,
            stt_latency_ms=session.metrics.stt_latency_ms,
            tts_latency_ms=session.metrics.tts_latency_ms,
        )

        return Result.ok(metrics_dto)
