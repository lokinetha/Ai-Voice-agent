"""
UpdateAgent Command and CommandHandler.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.kernel.cqrs import Command, CommandHandler
from shared.kernel.result import Error, Result
from shared.kernel.unit_of_work import UnitOfWork
from shared.kernel.value_objects import AgentId, Language, PlaybookId, PromptId

from agent.application.dto.agent_dto import AgentDTO
from agent.application.mappers.agent_mapper import AgentMapper
from agent.domain.repositories.agent_repository import AgentRepository
from agent.domain.value_objects.agent_llm_config import AgentLLMConfig
from agent.domain.value_objects.agent_voice_config import AgentVoiceConfig


@dataclass(frozen=True)
class UpdateAgentCommand(Command):
    """Command requesting updates to an Agent's configurations."""

    agent_id: str
    name: str | None = None
    playbook_id: str | None = None
    prompt_id: str | None = None
    tts_provider: str | None = None
    voice_id: str | None = None
    language: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    temperature: float | None = None


class UpdateAgentHandler(CommandHandler[UpdateAgentCommand, AgentDTO]):
    """Handler executing UpdateAgentCommand."""

    def __init__(
        self,
        agent_repository: AgentRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._agent_repo = agent_repository
        self._uow = unit_of_work

    async def handle(self, command: UpdateAgentCommand) -> Result[AgentDTO]:
        """Execute Agent updates."""
        agent = await self._agent_repo.get_by_id(AgentId(command.agent_id))
        if agent is None:
            return Result.fail(Error("NOT_FOUND", f"Agent '{command.agent_id}' not found"))

        if command.name is not None:
            res = agent.update_name(command.name)
            if res.is_failure:
                return Result.fail(res.error)

        if command.playbook_id is not None:
            agent.set_playbook_id(PlaybookId(command.playbook_id))

        if command.prompt_id is not None:
            agent.set_prompt_id(PromptId(command.prompt_id))

        if command.tts_provider is not None or command.voice_id is not None or command.language is not None:
            current_voice = agent.voice_config
            new_voice = AgentVoiceConfig(
                tts_provider=command.tts_provider or current_voice.tts_provider,
                voice_id=command.voice_id or current_voice.voice_id,
                speed=current_voice.speed,
                pitch=current_voice.pitch,
                language=Language(command.language) if command.language else current_voice.language,
            )
            agent.update_voice_config(new_voice)

        if command.llm_provider is not None or command.llm_model is not None or command.temperature is not None:
            current_llm = agent.llm_config
            new_llm = AgentLLMConfig(
                provider=command.llm_provider or current_llm.provider,
                model=command.llm_model or current_llm.model,
                temperature=command.temperature if command.temperature is not None else current_llm.temperature,
                max_tokens=current_llm.max_tokens,
                context_window=current_llm.context_window,
            )
            agent.update_llm_config(new_llm)

        async with self._uow:
            await self._agent_repo.save(agent)
            await self._uow.commit()

        return Result.ok(AgentMapper.to_dto(agent))
