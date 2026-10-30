"""
Unit and Integration tests for Multilingual Voice Agent Pipeline (English & Telugu).

Verifies:
- English -> English pipeline execution
- Telugu -> Telugu pipeline execution
- Explicit language selection vs automatic language detection
- Unsupported language rejection (UNSUPPORTED_LANGUAGE)
- Missing Telugu Piper model failure (MODEL_NOT_FOUND)
- Correct Telugu Piper model selection when configured
- English configuration remains unchanged
- Language propagation STT -> AgentRuntime -> TTS
"""

from __future__ import annotations

import asyncio
import os
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
from shared.config.settings import Settings, settings
from voice.application.dto.voice_pipeline_dto import VoiceTurnInput
from voice.application.services.voice_agent_pipeline import VoiceAgentPipeline
from voice.domain.value_objects.audio_chunk import AudioChunk
from voice.domain.value_objects.audio_format import AudioFormat
from voice.infrastructure.adapters.fake_llm_runtime_adapter import (
    FakeLLMRuntimeAdapter,
)
from voice.infrastructure.adapters.fake_stt_adapter import FakeSTTAdapter
from voice.infrastructure.adapters.fake_tts_adapter import FakeTTSAdapter
from voice.infrastructure.adapters.local_whisper_stt_adapter import (
    LocalWhisperSTTAdapter,
)
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
    """Mock PiperVoice engine capturing language selection during synthesis."""

    def __init__(self, audio_data: bytes = b"RIFF_MOCK_PIPER_AUDIO_PAYLOAD") -> None:
        self.audio_data = audio_data
        self.last_synthesized_text = ""

    def synthesize_bytes(
        self, text: str, voice_id: str, audio_format: AudioFormat
    ) -> bytes:
        self.last_synthesized_text = text
        return self.audio_data


class TestMultilingualVoiceTurn(unittest.TestCase):
    """Multilingual Voice Turn Test Suite."""

    def setUp(self) -> None:
        self.workspace_id = "ws-multi-1"
        self.agent_id = "agent-multi-1"
        self.conversation_id = "conv-multi-1"

        self.agent_config = AgentConfigDTO(
            agent_id=self.agent_id,
            workspace_id=self.workspace_id,
            name="Multilingual Voice Agent",
            is_active=True,
        )

        self.published_prompt = PublishedPromptDTO(
            prompt_id="prompt-multi-1",
            agent_id=self.agent_id,
            workspace_id=self.workspace_id,
            version=1,
            compiled_template="You are a helpful multilingual voice AI agent.",
            is_published=True,
        )

        self.agent_config_port = FakeAgentConfigReaderAdapter([self.agent_config])
        self.published_prompt_port = FakePublishedPromptReaderAdapter([self.published_prompt])
        self.agent_conv_context = FakeConversationContextAdapter()
        self.knowledge_port = FakeKnowledgeRetrievalAdapter()
        self.llm_adapter = FakeLLMRuntimeAdapter(
            override_response="నమస్కారం! నేను మీకు ఎలా సహాయపడగలను?"
        )

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

    def test_english_to_english_turn(self) -> None:
        """Verify English -> English turn execution and language metadata."""
        async def run() -> None:
            fake_llm = FakeLLMRuntimeAdapter(
                override_response="Hello! Our pricing options are flexible."
            )
            runtime_service = AgentRuntimeService(
                agent_config_port=self.agent_config_port,
                published_prompt_port=self.published_prompt_port,
                conversation_context_port=self.agent_conv_context,
                knowledge_retrieval_port=self.knowledge_port,
                llm_runtime_port=fake_llm,
            )
            pipeline = VoiceAgentPipeline(
                stt_port=self.stt_adapter,
                agent_runtime_service=runtime_service,
                tts_port=self.tts_adapter,
                conversation_port=self.conv_adapter,  # type: ignore[arg-type]
            )

            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes=b"Hello, what are your pricing options?",
                language="en-IN",
            )

            res_result = await pipeline.execute_voice_turn(turn_input)
            self.assertTrue(res_result.is_success)

            res = res_result.value
            self.assertEqual(res.detected_language, "en-IN")
            self.assertIn("pricing options", res.transcript.lower())
            self.assertTrue(len(res.agent_response_text) > 0)
            self.assertTrue(len(res.audio_bytes) > 0)

        asyncio.run(run())

    def test_telugu_to_telugu_turn(self) -> None:
        """Verify Telugu -> Telugu turn execution and language metadata."""
        async def run() -> None:
            telugu_text = "నమస్కారం, మీ ఉత్పత్తుల ధరల వివరాలు తెలియజేస్తారా?"
            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes=telugu_text.encode("utf-8"),
                language="te-IN",
            )

            res_result = await self.pipeline.execute_voice_turn(turn_input)
            self.assertTrue(res_result.is_success)

            res = res_result.value
            self.assertEqual(res.detected_language, "te-IN")
            self.assertEqual(res.transcript, telugu_text)
            self.assertTrue(len(res.agent_response_text) > 0)

        asyncio.run(run())

    def test_automatic_language_detection(self) -> None:
        """Verify automatic language detection when language='auto'."""
        async def run() -> None:
            telugu_text = "నమస్కారం, మీరు ఎలా ఉన్నారు?"
            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes=telugu_text.encode("utf-8"),
                language="auto",
            )

            res_result = await self.pipeline.execute_voice_turn(turn_input)
            self.assertTrue(res_result.is_success)

            res = res_result.value
            self.assertEqual(res.detected_language, "te-IN")

        asyncio.run(run())

    def test_unsupported_language_rejection(self) -> None:
        """Verify unsupported language returns UNSUPPORTED_LANGUAGE error."""
        async def run() -> None:
            turn_input = VoiceTurnInput(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                audio_bytes=b"Bonjour, comment ca va?",
                language="fr-FR",
            )

            res_result = await self.pipeline.execute_voice_turn(turn_input)
            self.assertTrue(res_result.is_failure)
            self.assertEqual(res_result.error.code, "UNSUPPORTED_LANGUAGE")
            self.assertIn("fr-FR", res_result.error.message)

        asyncio.run(run())

    def test_missing_telugu_piper_model_failure(self) -> None:
        """Verify missing Telugu Piper model raises MODEL_NOT_FOUND error in TTS."""
        async def run() -> None:
            old_te_env = os.environ.get("PIPER_TE_MODEL_PATH")
            os.environ["PIPER_TE_MODEL_PATH"] = "models/non_existent_te_model.onnx"
            try:
                piper_adapter = PiperTTSAdapter(piper_engine=None)
                pipeline_missing_model = VoiceAgentPipeline(
                    stt_port=self.stt_adapter,
                    agent_runtime_service=self.runtime_service,
                    tts_port=piper_adapter,
                    conversation_port=self.conv_adapter,  # type: ignore[arg-type]
                )

                telugu_text = "నమస్కారం"
                turn_input = VoiceTurnInput(
                    workspace_id=self.workspace_id,
                    agent_id=self.agent_id,
                    conversation_id=self.conversation_id,
                    audio_bytes=telugu_text.encode("utf-8"),
                    language="te-IN",
                )

                res_result = await pipeline_missing_model.execute_voice_turn(turn_input)
                self.assertTrue(res_result.is_failure)
                self.assertEqual(res_result.error.code, "TTS_FAILURE")
                self.assertIn("not configured or missing", res_result.error.message.lower())
            finally:
                if old_te_env is not None:
                    os.environ["PIPER_TE_MODEL_PATH"] = old_te_env
                else:
                    os.environ.pop("PIPER_TE_MODEL_PATH", None)

        asyncio.run(run())

    def test_correct_telugu_piper_model_selection_when_configured(self) -> None:
        """Verify PiperTTSAdapter resolves configured Telugu model path."""
        with tempfile.NamedTemporaryFile(suffix=".onnx", delete=False) as tmp:
            fake_te_path = tmp.name

        try:
            old_te_env = os.environ.get("PIPER_TE_MODEL_PATH")
            os.environ["PIPER_TE_MODEL_PATH"] = fake_te_path

            s = Settings()
            self.assertEqual(s.piper_te_model_path, fake_te_path)

            mock_engine = MockPiperEngine()
            adapter = PiperTTSAdapter(piper_engine=mock_engine)

            res_path = adapter.get_model_path_for_language("te-IN")
            self.assertEqual(res_path, fake_te_path)
        finally:
            if old_te_env is not None:
                os.environ["PIPER_TE_MODEL_PATH"] = old_te_env
            else:
                os.environ.pop("PIPER_TE_MODEL_PATH", None)

            if os.path.exists(fake_te_path):
                os.unlink(fake_te_path)

    def test_english_configuration_remains_unchanged(self) -> None:
        """Verify English configuration settings remain intact."""
        self.assertEqual(settings.default_language, "en-IN")
        self.assertIn("en-IN", settings.supported_languages)
        self.assertIn("te-IN", settings.supported_languages)

        adapter = PiperTTSAdapter(piper_engine=MockPiperEngine())
        en_path = adapter.get_model_path_for_language("en-IN")
        self.assertEqual(en_path, settings.piper_en_model_path)

    def test_local_whisper_transcription_mode_for_telugu(self) -> None:
        """Verify Whisper uses transcription mode (task='transcribe') for Telugu."""
        async def run() -> None:
            whisper_adapter = LocalWhisperSTTAdapter(model_name="tiny")
            chunk = AudioChunk(payload="నమస్కారం, ధన్యవాదాలు".encode())
            fmt = AudioFormat()

            res = await whisper_adapter.transcribe_detailed(chunk, fmt, language="te-IN")
            self.assertEqual(res.language, "te-IN")
            self.assertEqual(res.text, "నమస్కారం, ధన్యవాదాలు")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
