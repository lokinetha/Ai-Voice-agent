"""
MultiTurnVoicePipeline Application Orchestrator for Multi-Turn Voice Conversations.

Orchestrates sequential multi-turn voice execution over the SAME Conversation aggregate,
preserving workspace_id, agent_id, conversation_id, correlation_id, and full turn history.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from shared.kernel.result import Error, Result

from voice.application.dto.voice_pipeline_dto import (
    VoiceTurnInput,
    VoiceTurnResult,
)
from voice.application.services.voice_agent_pipeline import VoiceAgentPipeline

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MultiTurnVoiceResult:
    """Result returned by MultiTurnVoicePipeline for a complete conversation session."""

    workspace_id: str
    agent_id: str
    conversation_id: str
    correlation_id: str
    turn_results: list[VoiceTurnResult] = field(default_factory=list)
    total_turns: int = 0
    total_duration_ms: float = 0.0


class MultiTurnVoicePipeline:
    """Application service coordinating sequential multi-turn voice conversations."""

    def __init__(self, single_turn_pipeline: VoiceAgentPipeline) -> None:
        self._pipeline = single_turn_pipeline

    async def execute_multi_turn_conversation(
        self,
        workspace_id: str,
        agent_id: str,
        conversation_id: str,
        turn_inputs: list[VoiceTurnInput],
        correlation_id: str | None = None,
    ) -> Result[MultiTurnVoiceResult]:
        """Execute a sequence of voice turns within the SAME Conversation."""
        if not workspace_id or not agent_id or not conversation_id:
            return Result.fail(
                Error("VALIDATION_ERROR", "workspace_id, agent_id, and conversation_id required")
            )

        if not turn_inputs:
            return Result.fail(
                Error("INVALID_INPUT", "turn_inputs list cannot be empty")
            )

        corr_id = correlation_id or f"{workspace_id}:{conversation_id}"
        turn_results: list[VoiceTurnResult] = []
        total_duration = 0.0

        for idx, t_input in enumerate(turn_inputs, start=1):
            effective_input = VoiceTurnInput(
                workspace_id=workspace_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                audio_bytes=t_input.audio_bytes,
                audio_file_path=t_input.audio_file_path,
                output_audio_path=t_input.output_audio_path,
                correlation_id=corr_id,
                voice_id=t_input.voice_id,
                language=t_input.language,
            )

            res = await self._pipeline.execute_voice_turn(effective_input)
            if res.is_failure:
                logger.warning("Multi-turn voice conversation turn #%d failed: %s", idx, res.error.message)
                return Result.fail(
                    Error(
                        res.error.code,
                        f"Multi-turn conversation failed at turn #{idx}: {res.error.message}",
                    )
                )

            turn_result = res.value
            turn_results.append(turn_result)
            total_duration += turn_result.total_latency_ms

        return Result.ok(
            MultiTurnVoiceResult(
                workspace_id=workspace_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                correlation_id=corr_id,
                turn_results=turn_results,
                total_turns=len(turn_results),
                total_duration_ms=round(total_duration, 2),
            )
        )
