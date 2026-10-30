"""
Multi-turn E2E Local Execution Script.
"""

from __future__ import annotations

import asyncio

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
from voice.infrastructure.adapters.faster_whisper_stt_adapter import (
    FasterWhisperSTTAdapter,
)
from voice.infrastructure.adapters.in_memory_conversation_adapter import (
    InMemoryConversationAdapter,
)
from voice.infrastructure.adapters.piper_tts_adapter import PiperTTSAdapter


async def main() -> None:
    print("=" * 60)
    print("  Multi-Turn Voice Agent Pipeline E2E Runner")
    print("=" * 60)

    conv_adapter = InMemoryConversationAdapter()
    stt = FasterWhisperSTTAdapter()
    tts = PiperTTSAdapter()
    llm = resolve_llm_adapter(settings)

    agent_cfg = FakeAgentConfigReaderAdapter([
        AgentConfigDTO(
            agent_id="agent-1",
            workspace_id="ws-1",
            name="Dev MultiTurn Agent",
            is_active=True,
        )
    ])
    prompt = FakePublishedPromptReaderAdapter([
        PublishedPromptDTO(
            prompt_id="prompt-1",
            agent_id="agent-1",
            workspace_id="ws-1",
            version=1,
            compiled_template="You are a helpful multi-turn voice AI assistant.",
            is_published=True,
        )
    ])

    runtime_container = AgentRuntimeContainer(
        agent_config_port=agent_cfg,
        published_prompt_port=prompt,
        conversation_context_port=conv_adapter,
        llm_runtime_port=llm,
    )

    single_pipeline = VoiceAgentPipeline(
        stt_port=stt,
        agent_runtime_service=runtime_container.runtime_service,
        tts_port=tts,
        conversation_port=conv_adapter,
    )

    multi_pipeline = MultiTurnVoicePipeline(single_pipeline)

    with open("sample_input.wav", "rb") as f:
        sample_audio = f.read()

    conversation_id = "e2e-multi-turn-conv-1"
    turn_inputs = [
        VoiceTurnInput(
            workspace_id="ws-1",
            agent_id="agent-1",
            conversation_id=conversation_id,
            audio_bytes=sample_audio,
            output_audio_path="mt_e2e_turn_1.wav",
            language="en-IN",
        ),
        VoiceTurnInput(
            workspace_id="ws-1",
            agent_id="agent-1",
            conversation_id=conversation_id,
            audio_bytes=sample_audio,
            output_audio_path="mt_e2e_turn_2.wav",
            language="en-IN",
        ),
    ]

    print("[STATUS] Executing Multi-Turn Voice Session...")
    result = await multi_pipeline.execute_multi_turn_conversation(
        workspace_id="ws-1",
        agent_id="agent-1",
        conversation_id=conversation_id,
        turn_inputs=turn_inputs,
    )

    if result.is_failure:
        print(f"[ERROR] Multi-turn execution failed: {result.error.message}")
        return

    mt_res = result.value
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
        print(f'    User Transcript: "{tr.transcript}"')
        print(f'    Agent Response : "{tr.agent_response_text}"')
        print(f"    Audio Output   : {tr.output_audio_path}")

    history = conv_adapter.store.get_history(conversation_id)
    print("\n" + "=" * 60)
    print(f"  Persisted Conversation History ({len(history)} Messages)")
    print("=" * 60)
    for msg in history:
        print(f'  [{msg["role"]}] {msg["content"][:80]}...')
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
