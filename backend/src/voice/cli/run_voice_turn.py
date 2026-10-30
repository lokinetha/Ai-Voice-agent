"""
Local Development CLI Entry Point for running an End-to-End Voice Turn.

Usage:
    python -m voice.cli.run_voice_turn --audio-path sample.wav --agent-id agent-1 --conversation-id conv-1 --workspace-id ws-1 --language te-IN --stt-provider faster-whisper
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from agent_runtime.application.dto.agent_runtime_dto import (
    AgentConfigDTO,
    PublishedPromptDTO,
)
from agent_runtime.bootstrap.dependency_injection import AgentRuntimeContainer
from agent_runtime.infrastructure.adapters.fake_agent_config_reader_adapter import (
    FakeAgentConfigReaderAdapter,
)
from agent_runtime.infrastructure.adapters.fake_published_prompt_reader_adapter import (
    FakePublishedPromptReaderAdapter,
)
from shared.config.settings import resolve_llm_adapter, settings

from voice.application.dto.voice_pipeline_dto import VoiceTurnInput
from voice.application.services.voice_agent_pipeline import VoiceAgentPipeline
from voice.domain.ports.llm_runtime_port import LLMRuntimePort
from voice.domain.ports.stt_port import STTPort
from voice.domain.ports.tts_port import TTSPort
from voice.infrastructure.adapters.conversation_adapter import ConversationAdapter
from voice.infrastructure.adapters.fake_llm_runtime_adapter import (
    FakeLLMRuntimeAdapter,
)
from voice.infrastructure.adapters.fake_stt_adapter import FakeSTTAdapter
from voice.infrastructure.adapters.fake_tts_adapter import FakeTTSAdapter
from voice.infrastructure.adapters.faster_whisper_stt_adapter import (
    FasterWhisperSTTAdapter,
)
from voice.infrastructure.adapters.local_tts_adapter import LocalTTSAdapter
from voice.infrastructure.adapters.local_whisper_stt_adapter import (
    LocalWhisperSTTAdapter,
)
from voice.infrastructure.adapters.piper_tts_adapter import PiperTTSAdapter


async def main_async(args: argparse.Namespace) -> int:
    """Asynchronous CLI main runner."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    stt_provider_choice = (args.stt_provider or settings.stt_provider).lower()
    tts_provider_choice = (args.provider or settings.tts_provider).lower()

    print("=" * 60)
    print("  Local Voice Agent Pipeline Runner")
    print("=" * 60)
    print(f"  Input Audio File : {args.audio_path}")
    print(f"  Workspace ID     : {args.workspace_id}")
    print(f"  Agent ID         : {args.agent_id}")
    print(f"  Conversation ID  : {args.conversation_id}")
    print(f"  Language Option  : {args.language}")
    print(f"  STT Provider     : {stt_provider_choice}")
    print(f"  TTS Provider     : {tts_provider_choice}")
    print(f"  Output Audio Path: {args.output_audio}")
    print("-" * 60)

    # 1. Initialize STT & TTS Adapters based on mode flags or Settings
    stt_adapter: STTPort
    tts_adapter: TTSPort

    if stt_provider_choice in ("faster-whisper", "faster_whisper"):
        stt_adapter = FasterWhisperSTTAdapter(
            model_path=args.whisper_model_path or settings.whisper_model_path
        )
    elif stt_provider_choice in ("local", "whisper"):
        stt_adapter = LocalWhisperSTTAdapter(model_name=args.whisper_model or settings.whisper_model)
    else:
        stt_adapter = FakeSTTAdapter()

    if tts_provider_choice == "piper":
        tts_adapter = PiperTTSAdapter(model_path=args.piper_model or settings.piper_en_model_path)
    elif tts_provider_choice == "local":
        tts_adapter = LocalTTSAdapter(voice_id=args.voice_id)
    else:
        tts_adapter = FakeTTSAdapter()

    # 2. Resolve LLM Adapter using shared Settings mechanism
    llm_adapter: LLMRuntimePort
    try:
        if tts_provider_choice == "fake" and stt_provider_choice == "fake":
            llm_adapter = FakeLLMRuntimeAdapter()
        else:
            llm_adapter = resolve_llm_adapter(settings)
            print(f"[INFO] Using Gemini LLM Adapter (Model: {settings.gemini_model}, Key: {settings.get_masked_api_key()})")
    except ValueError as err:
        print("\n[ERROR] Configuration Error:")
        print(f"  {err}")
        return 1

    # 3. Seed dev Agent config & published Prompt
    agent_config_adapter = FakeAgentConfigReaderAdapter([
        AgentConfigDTO(
            agent_id=args.agent_id,
            workspace_id=args.workspace_id,
            name="Dev Voice Agent",
            is_active=True,
        )
    ])
    prompt_adapter = FakePublishedPromptReaderAdapter([
        PublishedPromptDTO(
            prompt_id="prompt-dev",
            agent_id=args.agent_id,
            workspace_id=args.workspace_id,
            version=1,
            compiled_template="You are a helpful voice AI agent.",
            is_published=True,
        )
    ])

    # 4. Setup Agent Runtime & Conversation Container
    agent_runtime_container = AgentRuntimeContainer(
        agent_config_port=agent_config_adapter,
        published_prompt_port=prompt_adapter,
        llm_runtime_port=llm_adapter,
    )
    conv_adapter = ConversationAdapter(session=None)

    pipeline = VoiceAgentPipeline(
        stt_port=stt_adapter,
        agent_runtime_service=agent_runtime_container.runtime_service,
        tts_port=tts_adapter,
        conversation_port=conv_adapter,
    )

    # 5. Read or generate input audio payload
    audio_bytes = b""
    if not os.path.exists(args.audio_path):
        print(f"[WARN] Specified input file '{args.audio_path}' does not exist.")
        print("[INFO] Creating a sample development audio payload for demonstration...")
        audio_bytes = b"Hello! Can you tell me about your AI agent capabilities?"
    else:
        with open(args.audio_path, "rb") as f:
            audio_bytes = f.read()

    turn_input = VoiceTurnInput(
        workspace_id=args.workspace_id,
        agent_id=args.agent_id,
        conversation_id=args.conversation_id,
        audio_bytes=audio_bytes,
        output_audio_path=args.output_audio,
        language=args.language,
    )

    print("[STATUS] Executing End-to-End Voice Turn...")
    result = await pipeline.execute_voice_turn(turn_input)

    if result.is_failure:
        print("\n[ERROR] Voice turn execution failed!")
        print(f"  Code   : {result.error.code}")
        print(f"  Message: {result.error.message}")
        return 1

    res = result.value
    print("\n" + "=" * 60)
    print("  Execution Summary")
    print("=" * 60)
    print(f"  Detected Language   : {res.detected_language}")
    print(f'  User Transcript     : "{res.transcript}"')
    print(f'  Agent Response Text : "{res.agent_response_text}"')
    print(f"  Output Audio File   : {res.output_audio_path}")
    print(f"  Correlation ID      : {res.correlation_id}")
    print("-" * 60)
    print(f"  STT Latency         : {res.stt_latency_ms} ms")
    print(f"  LLM Latency         : {res.llm_latency_ms} ms")
    print(f"  TTS Latency         : {res.tts_latency_ms} ms")
    print(f"  Total Turn Latency  : {res.total_latency_ms} ms")
    print("=" * 60)
    return 0


def main() -> None:
    """CLI Entry point parser."""
    parser = argparse.ArgumentParser(
        description="Run local end-to-end Voice Agent Turn pipeline."
    )
    parser.add_argument(
        "--audio-path",
        "-i",
        default="sample_input.wav",
        help="Path to input audio file (WAV format)",
    )
    parser.add_argument(
        "--agent-id",
        "-a",
        default="agent-1",
        help="Target Agent ID",
    )
    parser.add_argument(
        "--conversation-id",
        "-c",
        default="conv-1",
        help="Active Conversation ID",
    )
    parser.add_argument(
        "--workspace-id",
        "-w",
        default="ws-1",
        help="Owning Workspace ID",
    )
    parser.add_argument(
        "--language",
        "-l",
        default="auto",
        help="Language configuration ('auto', 'en-IN', 'te-IN')",
    )
    parser.add_argument(
        "--output-audio",
        "-o",
        default="output_response.wav",
        help="File path to save output synthesized speech audio",
    )
    parser.add_argument(
        "--stt-provider",
        default="",
        help="STT provider implementation ('faster-whisper', 'local', 'fake')",
    )
    parser.add_argument(
        "--provider",
        "-p",
        default="",
        help="TTS provider implementation ('piper', 'local', 'fake')",
    )
    parser.add_argument(
        "--whisper-model",
        default="",
        help="Whisper model size ('tiny', 'base', 'small', 'medium', 'large-v3')",
    )
    parser.add_argument(
        "--whisper-model-path",
        default="",
        help="Path to local faster-whisper model directory",
    )
    parser.add_argument(
        "--piper-model",
        default="",
        help="Path to local Piper ONNX model file (.onnx)",
    )
    parser.add_argument(
        "--voice-id",
        default="default",
        help="TTS Voice ID model",
    )

    args = parser.parse_args()
    code = asyncio.run(main_async(args))
    sys.exit(code)


if __name__ == "__main__":
    main()
