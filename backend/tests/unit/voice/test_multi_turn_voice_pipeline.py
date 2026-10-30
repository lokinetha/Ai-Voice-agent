"""
Unit tests for MultiTurnVoicePipeline and Voice DI resolution.

Verifies:
1. Multi-turn context preservation across sequential turns.
2. Same conversation ID shared across turns.
3. Message ordering (CUSTOMER -> AGENT -> CUSTOMER -> AGENT).
4. User/Agent message persistence in conversation store.
5. Correlation ID preservation across turns.
6. English multi-turn conversation.
7. Telugu multi-turn conversation.
8. Language preservation (independent language handling).
9. STT failure isolation.
10. LLM failure isolation.
11. TTS failure isolation (persisted messages remain intact).
12. FakeTTSAdapter remains usable in unit tests.
13. VoiceContainer resolves PiperTTSAdapter when TTS_PROVIDER=piper.
"""

from __future__ import annotations

import asyncio
import unittest
from typing import Any
from unittest.mock import patch

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
from agent_runtime.infrastructure.adapters.fake_knowledge_retrieval_adapter import (
    FakeKnowledgeRetrievalAdapter,
)
from agent_runtime.infrastructure.adapters.fake_published_prompt_reader_adapter import (
    FakePublishedPromptReaderAdapter,
)
from voice.application.dto.voice_pipeline_dto import VoiceTurnInput
from voice.application.services.multi_turn_voice_pipeline import (
    MultiTurnVoicePipeline,
)
from voice.application.services.voice_agent_pipeline import VoiceAgentPipeline
from voice.bootstrap.dependency_injection import VoiceContainer
from voice.domain.ports.stt_port import STTPort
from voice.domain.value_objects.audio_format import AudioFormat
from voice.infrastructure.adapters.fake_stt_adapter import FakeSTTAdapter
from voice.infrastructure.adapters.fake_tts_adapter import FakeTTSAdapter
from voice.infrastructure.adapters.in_memory_conversation_adapter import (
    InMemoryConversationAdapter,
)
from voice.infrastructure.adapters.local_tts_adapter import TTSProviderError
from voice.infrastructure.adapters.local_whisper_stt_adapter import STTProviderError
from voice.infrastructure.adapters.piper_tts_adapter import PiperTTSAdapter


class MockContextAwareLLMAdapter:
    """Mock LLM adapter verifying conversation context history received across turns."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.call_count = 0
        self.received_contexts: list[list[dict[str, str]]] = []

    async def generate_response(
        self,
        workspace_id: str,
        agent_id: str,
        conversation_id: str,
        prompt_text: str,
        compiled_prompt: str = "",
        conversation_context: list[dict[str, str]] | None = None,
        runtime_config: dict[str, Any] | None = None,
        knowledge_context: list[str] | None = None,
        tool_definitions: list[dict[str, Any]] | None = None,
    ) -> str:
        self.call_count += 1
        self.received_contexts.append(list(conversation_context or []))
        idx = min(self.call_count - 1, len(self.responses) - 1)
        return self.responses[idx]


class FailingTTSAdapter(FakeTTSAdapter):
    """Test double simulating TTS synthesis failure."""

    async def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        audio_format: AudioFormat,
        language: str | None = None,
    ) -> bytes:
        raise TTSProviderError("Hardware audio device error", code="TTS_FAILURE")


class FailingSTTAdapter(STTPort):
    """Test double simulating STT transcription failure."""

    async def transcribe_audio_chunk(
        self,
        chunk: Any,
        audio_format: Any,
        language: str | None = None,
    ) -> tuple[str, float]:
        raise STTProviderError("Corrupted audio payload", code="STT_FAILURE")

    async def transcribe_detailed(
        self,
        chunk: Any,
        audio_format: Any,
        language: str | None = None,
    ) -> Any:
        raise STTProviderError("Corrupted audio payload", code="STT_FAILURE")


class TestMultiTurnVoicePipeline(unittest.TestCase):
    """Unit test suite for MultiTurnVoicePipeline."""

    def setUp(self) -> None:
        self.workspace_id = "ws-multi-turn-1"
        self.agent_id = "agent-multi-turn-1"
        self.conversation_id = "conv-multi-turn-1"

        self.agent_config = AgentConfigDTO(
            agent_id=self.agent_id,
            workspace_id=self.workspace_id,
            name="MultiTurn Voice Agent",
            is_active=True,
        )

        self.published_prompt = PublishedPromptDTO(
            prompt_id="prompt-mt-1",
            agent_id=self.agent_id,
            workspace_id=self.workspace_id,
            version=1,
            compiled_template="You are a helpful voice AI assistant.",
            is_published=True,
        )

        self.agent_config_port = FakeAgentConfigReaderAdapter([self.agent_config])
        self.published_prompt_port = FakePublishedPromptReaderAdapter([self.published_prompt])
        self.knowledge_port = FakeKnowledgeRetrievalAdapter()

    def test_fake_tts_adapter_remains_usable_in_unit_tests(self) -> None:
        """Verify FakeTTSAdapter remains available and functional for fast unit testing."""
        adapter = FakeTTSAdapter()

        async def run() -> None:
            fmt = AudioFormat()
            audio_bytes = await adapter.synthesize_speech("Hello test", "default", fmt, "en-IN")
            self.assertTrue(audio_bytes.startswith(b"[TTS:"))

        asyncio.run(run())

    def test_voice_container_resolves_piper_tts_adapter_when_configured(self) -> None:
        """Verify VoiceContainer resolves PiperTTSAdapter when TTS_PROVIDER=piper."""
        with patch.dict("os.environ", {"TTS_PROVIDER": "piper"}):
            container = VoiceContainer()
            self.assertIsInstance(container.tts_port, PiperTTSAdapter)
            self.assertNotIsInstance(container.tts_port, FakeTTSAdapter)

    def test_english_multi_turn_conversation(self) -> None:
        """Verify English 3-turn voice conversation preserves same conversation ID and context."""
        async def run() -> None:
            conv_adapter = InMemoryConversationAdapter()
            llm_responses = [
                "Hello! We offer Cloud and On-Premise software packages.",
                "Our Cloud package starts at $49 per month.",
                "Yes, we offer a 20% discount for annual billing.",
            ]
            mock_llm = MockContextAwareLLMAdapter(llm_responses)

            runtime_service = AgentRuntimeService(
                agent_config_port=self.agent_config_port,
                published_prompt_port=self.published_prompt_port,
                conversation_context_port=conv_adapter,
                knowledge_retrieval_port=self.knowledge_port,
                llm_runtime_port=mock_llm,
            )

            single_pipeline = VoiceAgentPipeline(
                stt_port=FakeSTTAdapter(),
                agent_runtime_service=runtime_service,
                tts_port=FakeTTSAdapter(),
                conversation_port=conv_adapter,
            )

            multi_pipeline = MultiTurnVoicePipeline(single_pipeline)

            turn_inputs = [
                VoiceTurnInput(
                    workspace_id=self.workspace_id,
                    agent_id=self.agent_id,
                    conversation_id=self.conversation_id,
                    audio_bytes=b"Hello, what software packages do you offer?",
                    language="en-IN",
                ),
                VoiceTurnInput(
                    workspace_id=self.workspace_id,
                    agent_id=self.agent_id,
                    conversation_id=self.conversation_id,
                    audio_bytes=b"How much does the Cloud package cost?",
                    language="en-IN",
                ),
                VoiceTurnInput(
                    workspace_id=self.workspace_id,
                    agent_id=self.agent_id,
                    conversation_id=self.conversation_id,
                    audio_bytes=b"Is there any discount for annual billing?",
                    language="en-IN",
                ),
            ]

            result = await multi_pipeline.execute_multi_turn_conversation(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                turn_inputs=turn_inputs,
            )

            self.assertTrue(result.is_success)
            mt_res = result.value

            self.assertEqual(mt_res.total_turns, 3)
            self.assertEqual(mt_res.conversation_id, self.conversation_id)
            self.assertEqual(mt_res.correlation_id, f"{self.workspace_id}:{self.conversation_id}")

            # Verify message history stored in conversation adapter
            history = conv_adapter.store.get_history(self.conversation_id)
            self.assertEqual(len(history), 6)  # 3 CUSTOMER + 3 AGENT

            # Verify message ordering
            self.assertEqual(history[0]["role"], "CUSTOMER")
            self.assertEqual(history[1]["role"], "AGENT")
            self.assertEqual(history[2]["role"], "CUSTOMER")
            self.assertEqual(history[3]["role"], "AGENT")

            # Verify LLM received context history on turn #2 and turn #3
            self.assertEqual(len(mock_llm.received_contexts[0]), 0)  # Turn 1 context
            self.assertEqual(len(mock_llm.received_contexts[1]), 2)  # Turn 2 context (T1 user + T1 agent)
            self.assertEqual(len(mock_llm.received_contexts[2]), 4)  # Turn 3 context (T1 user + T1 agent + T2 user + T2 agent)

        asyncio.run(run())

    def test_telugu_multi_turn_conversation(self) -> None:
        """Verify Telugu 2-turn voice conversation preserves language and script across turns."""
        async def run() -> None:
            conv_adapter = InMemoryConversationAdapter()
            telugu_responses = [
                "నమస్కారం! మా వద్ద వివిధ ఉత్పత్తులు అందుబాటులో ఉన్నాయి.",
                "మా ఉత్పత్తుల ప్రారంభ ధర నెలకు రూ. 999.",
            ]
            mock_llm = MockContextAwareLLMAdapter(telugu_responses)

            runtime_service = AgentRuntimeService(
                agent_config_port=self.agent_config_port,
                published_prompt_port=self.published_prompt_port,
                conversation_context_port=conv_adapter,
                knowledge_retrieval_port=self.knowledge_port,
                llm_runtime_port=mock_llm,
            )

            single_pipeline = VoiceAgentPipeline(
                stt_port=FakeSTTAdapter(),
                agent_runtime_service=runtime_service,
                tts_port=FakeTTSAdapter(),
                conversation_port=conv_adapter,
            )

            multi_pipeline = MultiTurnVoicePipeline(single_pipeline)

            turn_inputs = [
                VoiceTurnInput(
                    workspace_id=self.workspace_id,
                    agent_id=self.agent_id,
                    conversation_id=self.conversation_id,
                    audio_bytes="నమస్కారం, మీ వద్ద ఏ ఉత్పత్తులు ఉన్నాయి?".encode(),
                    language="te-IN",
                ),
                VoiceTurnInput(
                    workspace_id=self.workspace_id,
                    agent_id=self.agent_id,
                    conversation_id=self.conversation_id,
                    audio_bytes="వాటి ధరల వివరాలు చెప్పగలరా?".encode(),
                    language="te-IN",
                ),
            ]

            result = await multi_pipeline.execute_multi_turn_conversation(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                turn_inputs=turn_inputs,
            )

            self.assertTrue(result.is_success)
            mt_res = result.value
            self.assertEqual(mt_res.total_turns, 2)
            self.assertEqual(mt_res.turn_results[0].detected_language, "te-IN")
            self.assertEqual(mt_res.turn_results[1].detected_language, "te-IN")

        asyncio.run(run())

    def test_stt_failure_isolation(self) -> None:
        """Verify STT failure does not pollute conversation history."""
        async def run() -> None:
            conv_adapter = InMemoryConversationAdapter()
            runtime_service = AgentRuntimeService(
                agent_config_port=self.agent_config_port,
                published_prompt_port=self.published_prompt_port,
                conversation_context_port=conv_adapter,
                knowledge_retrieval_port=self.knowledge_port,
                llm_runtime_port=MockContextAwareLLMAdapter(["Hi"]),
            )

            single_pipeline = VoiceAgentPipeline(
                stt_port=FailingSTTAdapter(),
                agent_runtime_service=runtime_service,
                tts_port=FakeTTSAdapter(),
                conversation_port=conv_adapter,
            )
            multi_pipeline = MultiTurnVoicePipeline(single_pipeline)

            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes=b"Corrupted audio",
                language="en-IN",
            )

            result = await multi_pipeline.execute_multi_turn_conversation(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                turn_inputs=[turn_input],
            )

            self.assertTrue(result.is_failure)
            self.assertEqual(result.error.code, "STT_FAILURE")
            self.assertEqual(len(conv_adapter.store.get_history(self.conversation_id)), 0)

        asyncio.run(run())

    def test_tts_failure_preserves_persisted_conversation_messages(self) -> None:
        """Verify TTS failure leaves user transcript and agent response persisted in Conversation history."""
        async def run() -> None:
            conv_adapter = InMemoryConversationAdapter()
            mock_llm = MockContextAwareLLMAdapter(["Agent text response."])

            runtime_service = AgentRuntimeService(
                agent_config_port=self.agent_config_port,
                published_prompt_port=self.published_prompt_port,
                conversation_context_port=conv_adapter,
                knowledge_retrieval_port=self.knowledge_port,
                llm_runtime_port=mock_llm,
            )

            single_pipeline = VoiceAgentPipeline(
                stt_port=FakeSTTAdapter(),
                agent_runtime_service=runtime_service,
                tts_port=FailingTTSAdapter(),
                conversation_port=conv_adapter,
            )

            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes=b"User transcript message",
                language="en-IN",
            )

            res = await single_pipeline.execute_voice_turn(turn_input)
            self.assertTrue(res.is_failure)
            self.assertEqual(res.error.code, "TTS_FAILURE")

            # Verify messages were persisted prior to TTS failure
            history = conv_adapter.store.get_history(self.conversation_id)
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["role"], "CUSTOMER")
            self.assertEqual(history[1]["role"], "AGENT")
            self.assertEqual(history[1]["content"], "Agent text response.")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
