"""
Local Development CLI Entry Point for running a Multi-Turn Voice Conversation.

Usage:
    python -m voice.cli.run_multi_turn_voice_turn --audio-path sample_input.wav --turns 2 --language en-IN
    python -m voice.cli.run_multi_turn_voice_turn --audio-path telugu_input.wav --turns 2 --language te-IN
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import wave

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
from voice.application.services.multi_turn_voice_pipeline import (
    MultiTurnVoicePipeline,
)
from voice.application.services.voice_agent_pipeline import VoiceAgentPipeline
from voice.domain.ports.llm_runtime_port import LLMRuntimePort
from voice.domain.ports.stt_port import STTPort
from voice.domain.ports.tts_port import TTSPort
from voice.infrastructure.adapters.fake_llm_runtime_adapter import (
    FakeLLMRuntimeAdapter,
)
from voice.infrastructure.adapters.fake_stt_adapter import FakeSTTAdapter
from voice.infrastructure.adapters.fake_tts_adapter import FakeTTSAdapter
from voice.infrastructure.adapters.faster_whisper_stt_adapter import (
    FasterWhisperSTTAdapter,
)
from voice.infrastructure.adapters.in_memory_conversation_adapter import (
    InMemoryConversationAdapter,
)
from voice.infrastructure.adapters.local_tts_adapter import LocalTTSAdapter
from voice.infrastructure.adapters.local_whisper_stt_adapter import (
    LocalWhisperSTTAdapter,
)
from voice.infrastructure.adapters.piper_tts_adapter import PiperTTSAdapter


async def main_async(args: argparse.Namespace) -> int:
    """Asynchronous CLI multi-turn runner."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    stt_provider_choice = (args.stt_provider or settings.stt_provider).lower()
    tts_provider_choice = (args.provider or settings.tts_provider).lower()

    print("=" * 60)
    print("  Local Multi-Turn Voice Agent Pipeline Runner")
    print("=" * 60)
    print(f"  Input Audio File : {args.audio_path}")
    print(f"  Workspace ID     : {args.workspace_id}")
    print(f"  Agent ID         : {args.agent_id}")
    print(f"  Conversation ID  : {args.conversation_id}")
    print(f"  Language Option  : {args.language}")
    print(f"  STT Provider     : {stt_provider_choice}")
    print(f"  TTS Provider     : {tts_provider_choice}")
    print(f"  Requested Turns  : {args.turns}")
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
            name="Dev Multi-Turn Voice Agent",
            is_active=True,
        )
    ])
    prompt_adapter = FakePublishedPromptReaderAdapter([
        PublishedPromptDTO(
            prompt_id="prompt-dev-mt",
            agent_id=args.agent_id,
            workspace_id=args.workspace_id,
            version=1,
            compiled_template="You are a helpful multi-turn voice AI assistant.",
            is_published=True,
        )
    ])

    # 4. Setup Agent Runtime & Conversation Adapter
    conv_adapter = InMemoryConversationAdapter()

    agent_runtime_container = AgentRuntimeContainer(
        agent_config_port=agent_config_adapter,
        published_prompt_port=prompt_adapter,
        conversation_context_port=conv_adapter,
        llm_runtime_port=llm_adapter,
    )

    single_pipeline = VoiceAgentPipeline(
        stt_port=stt_adapter,
        agent_runtime_service=agent_runtime_container.runtime_service,
        tts_port=tts_adapter,
        conversation_port=conv_adapter,
    )

    multi_pipeline = MultiTurnVoicePipeline(single_pipeline)

    # 5. Read input audio file bytes
    audio_bytes = b""
    if not os.path.exists(args.audio_path):
        print(f"[WARN] Specified input file '{args.audio_path}' does not exist.")
        print("[INFO] Creating a sample development audio payload for demonstration...")
        audio_bytes = b"Hello! Can you tell me about your AI agent capabilities?"
    else:
        with open(args.audio_path, "rb") as f:
            audio_bytes = f.read()

    turn_inputs: list[VoiceTurnInput] = []
    for idx in range(1, args.turns + 1):
        output_file = f"turn_{idx}_response.wav"
        turn_inputs.append(
            VoiceTurnInput(
                workspace_id=args.workspace_id,
                agent_id=args.agent_id,
                conversation_id=args.conversation_id,
                audio_bytes=audio_bytes,
                output_audio_path=output_file,
                language=args.language,
            )
        )

    print("[STATUS] Executing Multi-Turn Voice Session...")
    res_result = await multi_pipeline.execute_multi_turn_conversation(
        workspace_id=args.workspace_id,
        agent_id=args.agent_id,
        conversation_id=args.conversation_id,
        turn_inputs=turn_inputs,
    )

    if res_result.is_failure:
        print("\n[ERROR] Multi-turn voice execution failed!")
        print(f"  Code   : {res_result.error.code}")
        print(f"  Message: {res_result.error.message}")
        return 1

    mt_res = res_result.value
    print("\n" + "=" * 60)
    print("  Execution Summary")
    print("=" * 60)
    print(f"  Conversation ID   : {mt_res.conversation_id}")
    print(f"  Correlation ID    : {mt_res.correlation_id}")
    print(f"  Total Turns       : {mt_res.total_turns}")
    print(f"  Total Duration    : {mt_res.total_duration_ms} ms")
    print("-" * 60)

    for i, tr in enumerate(mt_res.turn_results, start=1):
        print(f"  Turn #{i}:")
        print(f"    Detected Language: {tr.detected_language}")
        print(f'    User Transcript  : "{tr.transcript}"')
        print(f'    Agent Response   : "{tr.agent_response_text}"')
        print(f"    Output Audio File: {tr.output_audio_path}")
        print(f"    STT Latency      : {tr.stt_latency_ms} ms")
        print(f"    LLM Latency      : {tr.llm_latency_ms} ms")
        print(f"    TTS Latency      : {tr.tts_latency_ms} ms")
        print(f"    Turn Total Time  : {tr.total_latency_ms} ms")
        print("-" * 60)

        # 6. Validate WAV Header & Audio Frames for real audio files
        if tr.output_audio_path and os.path.exists(tr.output_audio_path):
            with open(tr.output_audio_path, "rb") as f_check:
                header_bytes = f_check.read(4)

            if header_bytes != b"RIFF":
                print(f"    [WARN] Output file '{tr.output_audio_path}' does not have a RIFF header! (Got: {header_bytes!r})")
            else:
                try:
                    with wave.open(tr.output_audio_path, "rb") as wf:
                        print(
                            f"    [VALID WAV] channels={wf.getnchannels()}, "
                            f"sampwidth={wf.getsampwidth()}, rate={wf.getframerate()}, frames={wf.getnframes()}"
                        )
                except Exception as w_err:
                    print(f"    [ERROR] Failed to validate WAV audio frames: {w_err}")

    history = conv_adapter.store.get_history(args.conversation_id)
    print("\n" + "=" * 60)
    print(f"  Persisted Conversation History ({len(history)} Messages)")
    print("=" * 60)
    for msg in history:
        print(f'  [{msg["role"]}] {msg["content"][:90]}...')
    print("=" * 60)
    return 0


def main() -> None:
    """CLI Entry point parser."""
    parser = argparse.ArgumentParser(
        description="Run local multi-turn end-to-end Voice Agent Turn pipeline."
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
        default="conv-multi-1",
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
        "--turns",
        "-t",
        type=int,
        default=2,
        help="Number of sequential voice turns to execute",
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
