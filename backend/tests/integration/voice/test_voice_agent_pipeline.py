"""
Integration tests for VoiceAgentPipeline using fake test doubles.

Verifies end-to-end voice turn execution, error isolation (STT, LLM, TTS failures),
correlation ID propagation, and conversation history persistence without network,
hardware, or Gemini API keys.
"""

from __future__ import annotations

import asyncio
import tempfile
import unittest

from agent_runtime.application.dto.agent_runtime_dto import (
    AgentConfigDTO,
    PublishedPromptDTO,
)
from agent_runtime.application.services.agent_runtime_service import (
    AgentRuntimeService,
)
from agent_runtime.infrastructure.adapters.fake_agent_config_reader_adapter import (
    FakeAgentConfigReaderAdapter,
)
from agent_runtime.infrastructure.adapters.fake_conversation_context_adapter import (
    FakeConversationContextAdapter,
)
from agent_runtime.infrastructure.adapters.fake_knowledge_retrieval_adapter import (
    FakeKnowledgeRetrievalAdapter,
)
from agent_runtime.infrastructure.adapters.fake_published_prompt_reader_adapter import (
    FakePublishedPromptReaderAdapter,
)
from voice.application.commands.execute_voice_turn import (
    ExecuteVoiceTurnCommand,
    ExecuteVoiceTurnHandler,
)
from voice.application.dto.voice_pipeline_dto import VoiceTurnInput
from voice.application.services.voice_agent_pipeline import VoiceAgentPipeline
from voice.domain.ports.stt_port import STTPort
from voice.domain.ports.tts_port import TTSPort
from voice.domain.value_objects.audio_chunk import AudioChunk
from voice.domain.value_objects.audio_format import AudioFormat
from voice.infrastructure.adapters.fake_llm_runtime_adapter import (
    FakeLLMRuntimeAdapter,
)
from voice.infrastructure.adapters.fake_stt_adapter import FakeSTTAdapter
from voice.infrastructure.adapters.fake_tts_adapter import FakeTTSAdapter
from voice.infrastructure.adapters.local_tts_adapter import TTSProviderError
from voice.infrastructure.adapters.local_whisper_stt_adapter import STTProviderError


class FailingSTTAdapter(STTPort):
    """Test double simulating STT transcription failure."""

    async def transcribe_audio_chunk(
        self, chunk: AudioChunk, audio_format: AudioFormat
    ) -> tuple[str, float]:
        raise STTProviderError("STT audio corrupt or unsupported", code="INVALID_AUDIO")


class FailingTTSAdapter(TTSPort):
    """Test double simulating TTS synthesis failure."""

    async def synthesize_speech(
        self, text: str, voice_id: str, audio_format: AudioFormat
    ) -> bytes:
        raise TTSProviderError("TTS voice engine crashed", code="ENGINE_FAILURE")


class MockConversationAdapter:
    """Test double tracking messages appended to Conversation context."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str, str]] = []

    async def append_message_to_conversation(
        self, conversation_id: str, role: str, content: str
    ) -> str:
        self.messages.append((conversation_id, role, content))
        return f"msg-{len(self.messages)}"


class TestVoiceAgentPipeline(unittest.TestCase):
    """Integration test suite for VoiceAgentPipeline."""

    def setUp(self) -> None:
        self.workspace_id = "ws-pipe-1"
        self.agent_id = "agent-pipe-1"
        self.conversation_id = "conv-pipe-1"

        self.agent_config = AgentConfigDTO(
            agent_id=self.agent_id,
            workspace_id=self.workspace_id,
            name="Voice Assistant",
            is_active=True,
        )

        self.published_prompt = PublishedPromptDTO(
            prompt_id="prompt-pipe-1",
            agent_id=self.agent_id,
            workspace_id=self.workspace_id,
            version=1,
            compiled_template="You are a helpful voice AI agent.",
            is_published=True,
        )

        self.agent_config_port = FakeAgentConfigReaderAdapter([self.agent_config])
        self.published_prompt_port = FakePublishedPromptReaderAdapter([self.published_prompt])
        self.agent_conv_context = FakeConversationContextAdapter()
        self.knowledge_port = FakeKnowledgeRetrievalAdapter()
        self.llm_adapter = FakeLLMRuntimeAdapter()

        self.runtime_service = AgentRuntimeService(
            agent_config_port=self.agent_config_port,
            published_prompt_port=self.published_prompt_port,
            conversation_context_port=self.agent_conv_context,
            knowledge_retrieval_port=self.knowledge_port,
            llm_runtime_port=self.llm_adapter,
        )

        self.stt_adapter = FakeSTTAdapter()
        self.tts_adapter = FakeTTSAdapter()
        self.conv_adapter = MockConversationAdapter()

        self.pipeline = VoiceAgentPipeline(
            stt_port=self.stt_adapter,
            agent_runtime_service=self.runtime_service,
            tts_port=self.tts_adapter,
            conversation_port=self.conv_adapter,  # type: ignore[arg-type]
        )

    def test_complete_successful_voice_turn(self) -> None:
        async def run() -> None:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                out_path = tmp.name

            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes=b"Hello pipeline test",
                output_audio_path=out_path,
                correlation_id="corr-test-123",
            )

            result = await self.pipeline.execute_voice_turn(turn_input)
            self.assertTrue(result.is_success)

            res = result.value
            self.assertEqual(res.transcript, "Hello pipeline test")
            self.assertTrue(len(res.agent_response_text) > 0)
            self.assertTrue(len(res.audio_bytes) > 0)
            self.assertEqual(res.correlation_id, "corr-test-123")
            self.assertEqual(res.workspace_id, self.workspace_id)
            self.assertEqual(res.agent_id, self.agent_id)
            self.assertEqual(res.conversation_id, self.conversation_id)

            # Check conversation persistence (user transcript + agent response)
            self.assertEqual(len(self.conv_adapter.messages), 1)
            self.assertEqual(self.conv_adapter.messages[0][1], "CUSTOMER")

            agent_history = await self.agent_conv_context.get_conversation_history(self.conversation_id)
            self.assertEqual(len(agent_history), 1)
            self.assertEqual(agent_history[0].role, "AGENT")

        asyncio.run(run())

    def test_stt_failure_handling(self) -> None:
        async def run() -> None:
            failing_pipeline = VoiceAgentPipeline(
                stt_port=FailingSTTAdapter(),
                agent_runtime_service=self.runtime_service,
                tts_port=self.tts_adapter,
                conversation_port=self.conv_adapter,  # type: ignore[arg-type]
            )

            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes=b"Corrupt payload",
            )

            result = await failing_pipeline.execute_voice_turn(turn_input)
            self.assertTrue(result.is_failure)
            self.assertEqual(result.error.code, "STT_FAILURE")
            self.assertEqual(len(self.conv_adapter.messages), 0)

        asyncio.run(run())

    def test_llm_failure_handling(self) -> None:
        async def run() -> None:
            # Runtime configured with missing prompt agent
            failing_pipeline = VoiceAgentPipeline(
                stt_port=self.stt_adapter,
                agent_runtime_service=self.runtime_service,
                tts_port=self.tts_adapter,
                conversation_port=self.conv_adapter,  # type: ignore[arg-type]
            )

            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id="non-existent-agent",
                conversation_id=self.conversation_id,
                audio_bytes=b"Valid audio test",
            )

            result = await failing_pipeline.execute_voice_turn(turn_input)
            self.assertTrue(result.is_failure)
            self.assertEqual(result.error.code, "AGENT_RUNTIME_FAILURE")

            # User transcript was ALREADY recorded before LLM failure!
            self.assertEqual(len(self.conv_adapter.messages), 1)
            self.assertEqual(self.conv_adapter.messages[0][1], "CUSTOMER")

        asyncio.run(run())

    def test_tts_failure_handling(self) -> None:
        async def run() -> None:
            failing_tts_pipeline = VoiceAgentPipeline(
                stt_port=self.stt_adapter,
                agent_runtime_service=self.runtime_service,
                tts_port=FailingTTSAdapter(),
                conversation_port=self.conv_adapter,  # type: ignore[arg-type]
            )

            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes=b"Valid audio text",
            )

            result = await failing_tts_pipeline.execute_voice_turn(turn_input)
            self.assertTrue(result.is_failure)
            self.assertEqual(result.error.code, "TTS_FAILURE")

            # Conversation state MUST NOT be corrupted: transcript + agent response remain persisted!
            self.assertEqual(len(self.conv_adapter.messages), 1)
            self.assertEqual(self.conv_adapter.messages[0][1], "CUSTOMER")

            agent_history = await self.agent_conv_context.get_conversation_history(self.conversation_id)
            self.assertEqual(len(agent_history), 1)
            self.assertEqual(agent_history[0].role, "AGENT")

        asyncio.run(run())

    def test_execute_voice_turn_command_handler(self) -> None:
        async def run() -> None:
            handler = ExecuteVoiceTurnHandler(pipeline=self.pipeline)
            cmd = ExecuteVoiceTurnCommand(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes=b"Command handler input",
            )

            result = await handler.handle(cmd)
            self.assertTrue(result.is_success)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
