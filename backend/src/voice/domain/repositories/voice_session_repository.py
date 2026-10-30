"""
VoiceSessionRepository Domain Interface for Voice Bounded Context.
"""

from __future__ import annotations

from abc import abstractmethod

from shared.kernel.repository import Repository
from shared.kernel.value_objects import (
    AgentId,
    ConversationId,
    EntityId,
    WorkspaceId,
)

from voice.domain.entities.voice_session import VoiceSession


class VoiceSessionRepository(Repository[VoiceSession, EntityId]):
    """Domain Repository Interface for VoiceSession Aggregate Root."""

    @abstractmethod
    async def find_by_workspace(
        self, workspace_id: WorkspaceId
    ) -> list[VoiceSession]:
        """Find all VoiceSessions in target Workspace."""
        ...

    @abstractmethod
    async def find_by_conversation(
        self, conversation_id: ConversationId
    ) -> list[VoiceSession]:
        """Find all VoiceSessions associated with target Conversation."""
        ...

    @abstractmethod
    async def find_active_by_agent(
        self, agent_id: AgentId
    ) -> list[VoiceSession]:
        """Find active VoiceSessions for target Agent."""
        ...
