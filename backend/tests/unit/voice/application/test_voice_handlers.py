"""
Unit tests for Voice Application Command and Query Handlers.
"""

from __future__ import annotations

import asyncio
import unittest
from typing import Self

from shared.kernel.domain_event import DomainEvent
from shared.kernel.specification import Specification
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import (
    AgentId,
    ConversationId,
    EntityId,
    WorkspaceId,
)
from voice.application.commands.end_voice_session import (
    EndVoiceSessionCommand,
    EndVoiceSessionHandler,
)
from voice.application.commands.generate_agent_response import (
    GenerateAgentResponseCommand,
    GenerateAgentResponseHandler,
)
from voice.application.commands.process_audio_chunk import (
    ProcessAudioChunkCommand,
    ProcessAudioChunkHandler,
)
from voice.application.commands.process_transcript import (
    ProcessTranscriptCommand,
    ProcessTranscriptHandler,
)
from voice.application.commands.start_voice_session import (
    StartVoiceSessionCommand,
    StartVoiceSessionHandler,
)
from voice.application.commands.synthesize_response import (
    SynthesizeResponseCommand,
    SynthesizeResponseHandler,
)
from voice.application.queries.get_voice_session import (
    GetVoiceSessionHandler,
    GetVoiceSessionQuery,
)
from voice.application.queries.get_voice_session_metrics import (
    GetVoiceSessionMetricsHandler,
    GetVoiceSessionMetricsQuery,
)
from voice.domain.entities.voice_session import VoiceSession
from voice.domain.ports.conversation_port import ConversationPort
from voice.domain.repositories.voice_session_repository import (
    VoiceSessionRepository,
)
from voice.domain.services.voice_session_lifecycle_service import (
    VoiceSessionLifecycleService,
)
from voice.infrastructure.adapters.fake_audio_stream_adapter import (
    FakeAudioStreamAdapter,
)
from voice.infrastructure.adapters.fake_llm_runtime_adapter import (
    FakeLLMRuntimeAdapter,
)
from voice.infrastructure.adapters.fake_stt_adapter import FakeSTTAdapter
from voice.infrastructure.adapters.fake_telephony_adapter import (
    FakeTelephonyAdapter,
)
from voice.infrastructure.adapters.fake_tts_adapter import FakeTTSAdapter


class InMemoryVoiceSessionRepository(VoiceSessionRepository):
    """In-memory test double for VoiceSessionRepository."""

    def __init__(self) -> None:
        self.store: dict[str, VoiceSession] = {}

    async def get_by_id(self, id: EntityId) -> VoiceSession | None:
        return self.store.get(str(id.value))

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[VoiceSession]:
        return [s for s in self.store.values() if s.workspace_id == workspace_id]

    async def find_by_conversation(self, conversation_id: ConversationId) -> list[VoiceSession]:
        return [s for s in self.store.values() if s.conversation_id == conversation_id]

    async def find_active_by_agent(self, agent_id: AgentId) -> list[VoiceSession]:
        return [s for s in self.store.values() if s.agent_id == agent_id and s.status.is_active]

    async def save(self, aggregate: VoiceSession) -> None:
        self.store[str(aggregate.id.value)] = aggregate

    async def delete(self, aggregate: VoiceSession) -> None:
        self.store.pop(str(aggregate.id.value), None)

    async def find(self, spec: Specification[VoiceSession]) -> list[VoiceSession]:
        return [s for s in self.store.values() if spec.is_satisfied_by(s)]

    async def count(self, spec: Specification[VoiceSession]) -> int:
        return len(await self.find(spec))


class MockConversationPort(ConversationPort):
    """Test double for ConversationPort."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str, str]] = []

    async def append_message_to_conversation(
        self, conversation_id: str, role: str, content: str
    ) -> str:
        self.messages.append((conversation_id, role, content))
        return f"msg-{len(self.messages)}"


class DummyUnitOfWork(UnitOfWork):
    """Test double for UnitOfWork."""

    def __init__(self) -> None:
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass

    def collect_events(self) -> list[DomainEvent]:
        return []


class TestVoiceHandlers(unittest.TestCase):
    """Tests for Voice CQRS Handlers."""

    def setUp(self) -> None:
        self.repo = InMemoryVoiceSessionRepository()
        self.uow = DummyUnitOfWork()
        self.lifecycle_service = VoiceSessionLifecycleService()

        self.stt_adapter = FakeSTTAdapter()
        self.tts_adapter = FakeTTSAdapter()
        self.telephony_adapter = FakeTelephonyAdapter()
        self.stream_adapter = FakeAudioStreamAdapter()
        self.llm_adapter = FakeLLMRuntimeAdapter()
        self.conv_port = MockConversationPort()

    def test_full_voice_turn_loop_handlers(self) -> None:
        async def run() -> None:
            # 1. Start VoiceSession
            start_h = StartVoiceSessionHandler(self.repo, self.lifecycle_service, self.uow)
            start_res = await start_h.handle(
                StartVoiceSessionCommand(
                    workspace_id="ws-1",
                    agent_id="ag-1",
                    conversation_id="conv-1",
                )
            )
            self.assertTrue(start_res.is_success)
            s_id = start_res.value.id
            self.assertEqual(start_res.value.status, "ACTIVE")

            # 2. Process Audio Chunk
            audio_h = ProcessAudioChunkHandler(self.repo, self.stt_adapter, self.uow)
            chunk_res = await audio_h.handle(
                ProcessAudioChunkCommand(
                    session_id=s_id,
                    audio_bytes=b"Hello AI agent",
                )
            )
            self.assertTrue(chunk_res.is_success)
            self.assertGreater(len(chunk_res.value.turns), 0)

            # 3. Process Transcript to Conversation aggregate port
            trans_h = ProcessTranscriptHandler(self.repo, self.conv_port, self.uow)
            trans_res = await trans_h.handle(
                ProcessTranscriptCommand(
                    session_id=s_id,
                    transcript="Hello AI agent",
                )
            )
            self.assertTrue(trans_res.is_success)
            self.assertEqual(len(self.conv_port.messages), 1)

            # 4. Generate Agent Response
            gen_h = GenerateAgentResponseHandler(self.repo, self.llm_adapter, self.conv_port, self.uow)
            gen_res = await gen_h.handle(
                GenerateAgentResponseCommand(session_id=s_id, user_prompt="Hello AI agent")
            )
            self.assertTrue(gen_res.is_success)
            self.assertEqual(len(self.conv_port.messages), 2)

            # 5. Synthesize Response TTS
            synth_h = SynthesizeResponseHandler(self.repo, self.tts_adapter, self.stream_adapter, self.uow)
            synth_res = await synth_h.handle(SynthesizeResponseCommand(session_id=s_id))
            self.assertTrue(synth_res.is_success)

            # 6. End Session
            end_h = EndVoiceSessionHandler(self.repo, self.telephony_adapter, self.lifecycle_service, self.uow)
            end_res = await end_h.handle(EndVoiceSessionCommand(session_id=s_id))
            self.assertTrue(end_res.is_success)
            self.assertEqual(end_res.value.status, "ENDED")

            # 7. Query session & metrics
            get_h = GetVoiceSessionHandler(self.repo)
            get_res = await get_h.handle(GetVoiceSessionQuery(session_id=s_id))
            self.assertTrue(get_res.is_success)

            met_h = GetVoiceSessionMetricsHandler(self.repo)
            met_res = await met_h.handle(GetVoiceSessionMetricsQuery(session_id=s_id))
            self.assertTrue(met_res.is_success)
            self.assertGreater(met_res.value.total_turns, 0)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
