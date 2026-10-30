"""
Integration tests for MultiTurnVoicePipeline using local Voice adapters.

Runs multi-turn voice integration tests on GPU/CUDA and Piper ONNX when models are available.
Skips cleanly if model files are missing.
"""

from __future__ import annotations

import asyncio
import os
import unittest
import wave

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
from shared.config.settings import resolve_llm_adapter, settings
from voice.application.dto.voice_pipeline_dto import VoiceTurnInput
from voice.application.services.multi_turn_voice_pipeline import (
    MultiTurnVoicePipeline,
)
from voice.application.services.voice_agent_pipeline import VoiceAgentPipeline
from voice.infrastructure.adapters.faster_whisper_stt_adapter import (
    FasterWhisperSTTAdapter,
)
from voice.infrastructure.adapters.in_memory_conversation_adapter import (
    InMemoryConversationAdapter,
)
from voice.infrastructure.adapters.piper_tts_adapter import PiperTTSAdapter

# Model checks for integration test
WHISPER_MODEL_PATH = str(settings.project_root / "models" / "faster-whisper-large-v3")
HAS_WHISPER_MODEL = os.path.exists(WHISPER_MODEL_PATH)
HAS_PIPER_EN_MODEL = os.path.exists(settings.piper_en_model_path)
HAS_PIPER_TE_MODEL = os.path.exists(settings.piper_te_model_path)

TELUGU_WAV_PATH = str(settings.project_root / "telugu_input.wav")
ENGLISH_WAV_PATH = str(settings.project_root / "sample_input.wav")


@unittest.skipUnless(HAS_WHISPER_MODEL and HAS_PIPER_EN_MODEL, "faster-whisper large-v3 or Piper models not found on disk")
class TestMultiTurnVoicePipelineIntegration(unittest.TestCase):
    """Integration test suite for multi-turn voice pipeline."""

    def setUp(self) -> None:
        self.workspace_id = "ws-mt-integration"
        self.agent_id = "agent-mt-integration"

        self.agent_config = AgentConfigDTO(
            agent_id=self.agent_id,
            workspace_id=self.workspace_id,
            name="MultiTurn Integration Agent",
            is_active=True,
        )

        self.published_prompt = PublishedPromptDTO(
            prompt_id="prompt-mt-integ",
            agent_id=self.agent_id,
            workspace_id=self.workspace_id,
            version=1,
            compiled_template="You are a helpful voice AI assistant.",
            is_published=True,
        )

        self.agent_config_port = FakeAgentConfigReaderAdapter([self.agent_config])
        self.published_prompt_port = FakePublishedPromptReaderAdapter([self.published_prompt])
        self.knowledge_port = FakeKnowledgeRetrievalAdapter()

    def test_multi_turn_english_real_wav_output(self) -> None:
        """Integration test: 2-turn English voice conversation producing real RIFF/WAVE files."""
        if not os.path.exists(ENGLISH_WAV_PATH):
            self.skipTest(f"Audio file '{ENGLISH_WAV_PATH}' missing")

        with open(ENGLISH_WAV_PATH, "rb") as f:
            audio_bytes = f.read()

        conv_id = "conv-mt-english-real-wav"
        conv_adapter = InMemoryConversationAdapter()
        stt_adapter = FasterWhisperSTTAdapter(
            model_path=WHISPER_MODEL_PATH,
            device="cuda",
            compute_type="int8_float16",
        )
        tts_adapter = PiperTTSAdapter()
        llm_adapter = resolve_llm_adapter(settings)

        runtime_service = AgentRuntimeService(
            agent_config_port=self.agent_config_port,
            published_prompt_port=self.published_prompt_port,
            conversation_context_port=conv_adapter,
            knowledge_retrieval_port=self.knowledge_port,
            llm_runtime_port=llm_adapter,
        )

        single_pipeline = VoiceAgentPipeline(
            stt_port=stt_adapter,
            agent_runtime_service=runtime_service,
            tts_port=tts_adapter,
            conversation_port=conv_adapter,
        )

        multi_pipeline = MultiTurnVoicePipeline(single_pipeline)

        async def run() -> None:
            turn_inputs = [
                VoiceTurnInput(
                    workspace_id=self.workspace_id,
                    agent_id=self.agent_id,
                    conversation_id=conv_id,
                    audio_bytes=audio_bytes,
                    output_audio_path="turn_1_en_response.wav",
                    language="en-IN",
                ),
                VoiceTurnInput(
                    workspace_id=self.workspace_id,
                    agent_id=self.agent_id,
                    conversation_id=conv_id,
                    audio_bytes=audio_bytes,
                    output_audio_path="turn_2_en_response.wav",
                    language="en-IN",
                ),
            ]

            res_result = await multi_pipeline.execute_multi_turn_conversation(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=conv_id,
                turn_inputs=turn_inputs,
            )

            self.assertTrue(res_result.is_success)
            mt_res = res_result.value

            self.assertEqual(mt_res.total_turns, 2)
            self.assertEqual(mt_res.conversation_id, conv_id)

            history = conv_adapter.store.get_history(conv_id)
            self.assertEqual(len(history), 4)

            # Verify real WAV headers for both turn outputs
            for file_path in ["turn_1_en_response.wav", "turn_2_en_response.wav"]:
                self.assertTrue(os.path.exists(file_path))
                with open(file_path, "rb") as f_chk:
                    hdr = f_chk.read(4)
                self.assertEqual(hdr, b"RIFF", f"File '{file_path}' must begin with RIFF header")

                with wave.open(file_path, "rb") as wf:
                    self.assertGreater(wf.getnchannels(), 0)
                    self.assertGreater(wf.getsampwidth(), 0)
                    self.assertGreater(wf.getframerate(), 0)
                    self.assertGreater(wf.getnframes(), 0)

        asyncio.run(run())

    @unittest.skipUnless(HAS_PIPER_TE_MODEL, "Telugu Piper ONNX model missing on disk")
    def test_multi_turn_telugu_real_wav_output(self) -> None:
        """Integration test: 2-turn Telugu voice conversation producing real RIFF/WAVE files."""
        if not os.path.exists(TELUGU_WAV_PATH):
            self.skipTest(f"Audio file '{TELUGU_WAV_PATH}' missing")

        with open(TELUGU_WAV_PATH, "rb") as f:
            audio_bytes = f.read()

        conv_id = "conv-mt-telugu-real-wav"
        conv_adapter = InMemoryConversationAdapter()
        stt_adapter = FasterWhisperSTTAdapter(
            model_path=WHISPER_MODEL_PATH,
            device="cuda",
            compute_type="int8_float16",
        )
        tts_adapter = PiperTTSAdapter()
        llm_adapter = resolve_llm_adapter(settings)

        runtime_service = AgentRuntimeService(
            agent_config_port=self.agent_config_port,
            published_prompt_port=self.published_prompt_port,
            conversation_context_port=conv_adapter,
            knowledge_retrieval_port=self.knowledge_port,
            llm_runtime_port=llm_adapter,
        )

        single_pipeline = VoiceAgentPipeline(
            stt_port=stt_adapter,
            agent_runtime_service=runtime_service,
            tts_port=tts_adapter,
            conversation_port=conv_adapter,
        )

        multi_pipeline = MultiTurnVoicePipeline(single_pipeline)

        async def run() -> None:
            turn_inputs = [
                VoiceTurnInput(
                    workspace_id=self.workspace_id,
                    agent_id=self.agent_id,
                    conversation_id=conv_id,
                    audio_bytes=audio_bytes,
                    output_audio_path="turn_1_te_response.wav",
                    language="te-IN",
                ),
                VoiceTurnInput(
                    workspace_id=self.workspace_id,
                    agent_id=self.agent_id,
                    conversation_id=conv_id,
                    audio_bytes=audio_bytes,
                    output_audio_path="turn_2_te_response.wav",
                    language="te-IN",
                ),
            ]

            res_result = await multi_pipeline.execute_multi_turn_conversation(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=conv_id,
                turn_inputs=turn_inputs,
            )

            self.assertTrue(res_result.is_success)
            mt_res = res_result.value

            self.assertEqual(mt_res.total_turns, 2)
            self.assertEqual(mt_res.conversation_id, conv_id)

            history = conv_adapter.store.get_history(conv_id)
            self.assertEqual(len(history), 4)

            # Verify real WAV headers for both turn outputs
            for file_path in ["turn_1_te_response.wav", "turn_2_te_response.wav"]:
                self.assertTrue(os.path.exists(file_path))
                with open(file_path, "rb") as f_chk:
                    hdr = f_chk.read(4)
                self.assertEqual(hdr, b"RIFF", f"File '{file_path}' must begin with RIFF header")

                with wave.open(file_path, "rb") as wf:
                    self.assertGreater(wf.getnchannels(), 0)
                    self.assertGreater(wf.getsampwidth(), 0)
                    self.assertGreater(wf.getframerate(), 0)
                    self.assertGreater(wf.getnframes(), 0)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
