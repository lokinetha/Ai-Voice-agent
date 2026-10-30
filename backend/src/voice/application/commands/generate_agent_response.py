"""
GenerateAgentResponse Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import EntityId

from voice.application.dto.voice_dto import VoiceSessionDTO
from voice.application.mappers.voice_mapper import VoiceMapper
from voice.domain.ports.conversation_port import ConversationPort
from voice.domain.ports.llm_runtime_port import LLMRuntimePort
from voice.domain.repositories.voice_session_repository import (
    VoiceSessionRepository,
)


@dataclass(frozen=True)
class GenerateAgentResponseCommand(Command):
    """Command requesting AI Agent text response generation via LLMRuntimePort."""

    session_id: str
    user_prompt: str = ""


class GenerateAgentResponseHandler(CommandHandler[GenerateAgentResponseCommand, VoiceSessionDTO]):
    """Handler executing GenerateAgentResponseCommand via LLMRuntimePort & ConversationPort."""

    def __init__(
        self,
        session_repository: VoiceSessionRepository,
        llm_runtime_port: LLMRuntimePort,
        conversation_port: ConversationPort,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repo = session_repository
        self._llm = llm_runtime_port
        self._conv_port = conversation_port
        self._uow = unit_of_work

    async def handle(self, command: GenerateAgentResponseCommand) -> Result[VoiceSessionDTO]:
        """Execute GenerateAgentResponseCommand."""
        if not command.session_id:
            return Result.fail(Error("VALIDATION_ERROR", "session_id required"))

        session = await self._repo.get_by_id(EntityId(command.session_id))
        if session is None:
            return Result.fail(Error("NOT_FOUND", f"VoiceSession '{command.session_id}' not found"))

        # Identify latest transcript turn or fallback to prompt
        latest_turn = session.turns[-1] if session.turns else None
        prompt_text = command.user_prompt or (latest_turn.transcript if latest_turn else "Hello")

        # Generate LLM response via port
        response_text = await self._llm.generate_response(
            workspace_id=str(session.workspace_id.value),
            agent_id=str(session.agent_id.value),
            conversation_id=str(session.conversation_id.value),
            prompt_text=prompt_text,
        )

        # Record message in Conversation aggregate via port
        await self._conv_port.append_message_to_conversation(
            conversation_id=str(session.conversation_id.value),
            role="AGENT",
            content=response_text,
        )

        # Start agent turn in session
        agent_turn_res = session.start_turn("AGENT")
        if agent_turn_res.is_failure:
            return Result.fail(agent_turn_res.error)
        agent_turn = agent_turn_res.value

        session.record_agent_response(str(agent_turn.id.value), response_text)

        async with self._uow:
            await self._repo.save(session)
            await self._uow.commit()

        return Result.ok(VoiceMapper.to_dto(session))
