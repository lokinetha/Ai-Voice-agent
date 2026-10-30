"""
GetVoiceSession Query and QueryHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Query, QueryHandler
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import EntityId

from voice.application.dto.voice_dto import VoiceSessionDTO
from voice.application.mappers.voice_mapper import VoiceMapper
from voice.domain.repositories.voice_session_repository import (
    VoiceSessionRepository,
)


@dataclass(frozen=True)
class GetVoiceSessionQuery(Query):
    """Query requesting VoiceSession details by ID."""

    session_id: str


class GetVoiceSessionHandler(QueryHandler[GetVoiceSessionQuery, VoiceSessionDTO]):
    """Handler executing GetVoiceSessionQuery."""

    def __init__(self, session_repository: VoiceSessionRepository) -> None:
        self._repo = session_repository

    async def handle(self, query: GetVoiceSessionQuery) -> Result[VoiceSessionDTO]:
        """Execute GetVoiceSessionQuery."""
        if not query.session_id:
            return Result.fail(Error("VALIDATION_ERROR", "Session ID cannot be empty"))

        session = await self._repo.get_by_id(EntityId(query.session_id))
        if session is None:
            return Result.fail(Error("NOT_FOUND", f"VoiceSession '{query.session_id}' not found"))

        return Result.ok(VoiceMapper.to_dto(session))
