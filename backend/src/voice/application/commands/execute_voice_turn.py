"""
ExecuteVoiceTurn Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Result

from voice.application.dto.voice_pipeline_dto import (
    VoiceTurnInput,
    VoiceTurnResult,
)
from voice.application.services.voice_agent_pipeline import VoiceAgentPipeline


@dataclass(frozen=True)
class ExecuteVoiceTurnCommand(Command):
    """Command requesting execution of an end-to-end voice turn."""

    workspace_id: str
    agent_id: str
    conversation_id: str
    audio_bytes: bytes = b""
    audio_file_path: str = ""
    output_audio_path: str = ""
    correlation_id: str | None = None
    voice_id: str = "default"
    language: str | None = None


class ExecuteVoiceTurnHandler(CommandHandler[ExecuteVoiceTurnCommand, VoiceTurnResult]):
    """CQRS Handler executing ExecuteVoiceTurnCommand via VoiceAgentPipeline."""

    def __init__(self, pipeline: VoiceAgentPipeline) -> None:
        self._pipeline = pipeline

    async def handle(self, command: ExecuteVoiceTurnCommand) -> Result[VoiceTurnResult]:
        """Execute end-to-end voice turn pipeline."""
        turn_input = VoiceTurnInput(
            workspace_id=command.workspace_id,
            agent_id=command.agent_id,
            conversation_id=command.conversation_id,
            audio_bytes=command.audio_bytes,
            audio_file_path=command.audio_file_path,
            output_audio_path=command.output_audio_path,
            correlation_id=command.correlation_id,
            voice_id=command.voice_id,
            language=command.language,
        )
        return await self._pipeline.execute_voice_turn(turn_input)
