"""
Unit tests for language preservation across Multilingual Voice Pipeline.

Verifies:
- te-IN input -> Telugu-script LLM response accepted
- te-IN input -> English LLM response rejected with LANGUAGE_MISMATCH error
- en-IN input -> English response accepted
- Telugu text reaches Piper TTS when te-IN is selected
"""

from __future__ import annotations

import asyncio
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
from voice.application.dto.voice_pipeline_dto import VoiceTurnInput
from voice.application.services.voice_agent_pipeline import VoiceAgentPipeline
from voice.domain.value_objects.audio_format import AudioFormat
from voice.infrastructure.adapters.fake_llm_runtime_adapter import (
    FakeLLMRuntimeAdapter,
)
from voice.infrastructure.adapters.fake_stt_adapter import FakeSTTAdapter
from voice.infrastructure.adapters.fake_tts_adapter import FakeTTSAdapter
from voice.infrastructure.adapters.piper_tts_adapter import PiperTTSAdapter


class MockConversationAdapter:
    """Test double tracking messages appended to Conversation context."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str, str]] = []

    async def append_message_to_conversation(
        self, conversation_id: str, role: str, content: str
    ) -> str:
        self.messages.append((conversation_id, role, content))
        return f"msg-{len(self.messages)}"


class MockPiperEngine:
    """Mock PiperVoice engine capturing synthesized text and language."""

    def __init__(self) -> None:
        self.last_text = ""
        self.last_voice_id = ""

    def synthesize_bytes(
        self, text: str, voice_id: str, audio_format: AudioFormat
    ) -> bytes:
        self.last_text = text
        self.last_voice_id = voice_id
        return b"RIFF_MOCK_TELUGU_PIPER_WAV_PAYLOAD"


class TestLanguagePreservation(unittest.TestCase):
    """Unit test suite verifying language preservation rules."""

    def setUp(self) -> None:
        self.workspace_id = "ws-lang-1"
        self.agent_id = "agent-lang-1"
        self.conversation_id = "conv-lang-1"

        self.agent_config = AgentConfigDTO(
            agent_id=self.agent_id,
            workspace_id=self.workspace_id,
            name="Language Preservation Agent",
            is_active=True,
        )

        self.published_prompt = PublishedPromptDTO(
            prompt_id="prompt-lang-1",
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

    def test_telugu_input_with_telugu_llm_response_accepted(self) -> None:
        """Verify te-IN input with Telugu script response succeeds."""
        async def run() -> None:
            fake_llm = FakeLLMRuntimeAdapter(
                override_response="నమస్కారం! నేను మీకు ఎలా సహాయపడగలను?"
            )
            runtime_service = AgentRuntimeService(
                agent_config_port=self.agent_config_port,
                published_prompt_port=self.published_prompt_port,
                conversation_context_port=self.agent_conv_context,
                knowledge_retrieval_port=self.knowledge_port,
                llm_runtime_port=fake_llm,
            )
            conv_adapter = MockConversationAdapter()
            pipeline = VoiceAgentPipeline(
                stt_port=FakeSTTAdapter(),
                agent_runtime_service=runtime_service,
                tts_port=FakeTTSAdapter(),
                conversation_port=conv_adapter,  # type: ignore[arg-type]
            )

            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes="నమస్కారం".encode(),
                language="te-IN",
            )

            result = await pipeline.execute_voice_turn(turn_input)
            self.assertTrue(result.is_success)
            self.assertEqual(result.value.detected_language, "te-IN")
            self.assertEqual(
                result.value.agent_response_text,
                "నమస్కారం! నేను మీకు ఎలా సహాయపడగలను?",
            )

        asyncio.run(run())

    def test_telugu_input_with_english_llm_response_rejected_with_language_mismatch(self) -> None:
        """Verify te-IN input with English LLM response fails with LANGUAGE_MISMATCH."""
        async def run() -> None:
            fake_llm = FakeLLMRuntimeAdapter(
                override_response="Hello! I can help you with pricing details."
            )
            runtime_service = AgentRuntimeService(
                agent_config_port=self.agent_config_port,
                published_prompt_port=self.published_prompt_port,
                conversation_context_port=self.agent_conv_context,
                knowledge_retrieval_port=self.knowledge_port,
                llm_runtime_port=fake_llm,
            )
            conv_adapter = MockConversationAdapter()
            pipeline = VoiceAgentPipeline(
                stt_port=FakeSTTAdapter(),
                agent_runtime_service=runtime_service,
                tts_port=FakeTTSAdapter(),
                conversation_port=conv_adapter,  # type: ignore[arg-type]
            )

            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes="నమస్కారం".encode(),
                language="te-IN",
            )

            result = await pipeline.execute_voice_turn(turn_input)
            self.assertTrue(result.is_failure)
            self.assertEqual(result.error.code, "LANGUAGE_MISMATCH")
            self.assertIn("Expected Telugu script response", result.error.message)

        asyncio.run(run())

    def test_english_input_with_english_response_accepted(self) -> None:
        """Verify en-IN input with English response succeeds."""
        async def run() -> None:
            fake_llm = FakeLLMRuntimeAdapter(
                override_response="Hello! How can I assist you today?"
            )
            runtime_service = AgentRuntimeService(
                agent_config_port=self.agent_config_port,
                published_prompt_port=self.published_prompt_port,
                conversation_context_port=self.agent_conv_context,
                knowledge_retrieval_port=self.knowledge_port,
                llm_runtime_port=fake_llm,
            )
            conv_adapter = MockConversationAdapter()
            pipeline = VoiceAgentPipeline(
                stt_port=FakeSTTAdapter(),
                agent_runtime_service=runtime_service,
                tts_port=FakeTTSAdapter(),
                conversation_port=conv_adapter,  # type: ignore[arg-type]
            )

            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes=b"Hello assistant",
                language="en-IN",
            )

            result = await pipeline.execute_voice_turn(turn_input)
            self.assertTrue(result.is_success)
            self.assertEqual(result.value.detected_language, "en-IN")

        asyncio.run(run())

    def test_telugu_text_reaches_piper_when_te_in_selected(self) -> None:
        """Verify exact Telugu script text reaches Piper TTS engine when te-IN is selected."""
        async def run() -> None:
            telugu_llm_text = "ధన్యవాదాలు, మీ ప్రశ్న స్వీకరించబడింది."
            fake_llm = FakeLLMRuntimeAdapter(override_response=telugu_llm_text)
            runtime_service = AgentRuntimeService(
                agent_config_port=self.agent_config_port,
                published_prompt_port=self.published_prompt_port,
                conversation_context_port=self.agent_conv_context,
                knowledge_retrieval_port=self.knowledge_port,
                llm_runtime_port=fake_llm,
            )

            mock_piper = MockPiperEngine()
            piper_adapter = PiperTTSAdapter(piper_engine=mock_piper)
            conv_adapter = MockConversationAdapter()

            pipeline = VoiceAgentPipeline(
                stt_port=FakeSTTAdapter(),
                agent_runtime_service=runtime_service,
                tts_port=piper_adapter,
                conversation_port=conv_adapter,  # type: ignore[arg-type]
            )

            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes="ధన్యవాదాలు".encode(),
                language="te-IN",
            )

            result = await pipeline.execute_voice_turn(turn_input)
            self.assertTrue(result.is_success)
            self.assertEqual(mock_piper.last_text, telugu_llm_text)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
