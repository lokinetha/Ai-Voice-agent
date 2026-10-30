"""
AgentMapper for mapping between Domain Aggregates and Application DTOs.
"""

from __future__ import annotations

from agent.application.dto.agent_dto import (
    AgentDTO,
    AgentLLMConfigDTO,
    AgentMemoryConfigDTO,
    AgentPolicyDTO,
    AgentRuntimeConfigDTO,
    AgentToolDTO,
    AgentVoiceConfigDTO,
)
from agent.domain.entities.agent import Agent
from agent.domain.entities.agent_policy import AgentPolicy
from agent.domain.entities.agent_tool import AgentTool
from agent.domain.value_objects.agent_llm_config import AgentLLMConfig
from agent.domain.value_objects.agent_memory_config import AgentMemoryConfig
from agent.domain.value_objects.agent_runtime_config import AgentRuntimeConfig
from agent.domain.value_objects.agent_voice_config import AgentVoiceConfig


class AgentMapper:
    """Static mapper for Agent Aggregate Root ↔ DTO conversion."""

    @staticmethod
    def to_dto(agent: Agent) -> AgentDTO:
        """Map Agent aggregate root to AgentDTO."""
        return AgentDTO(
            id=str(agent.id.value),
            workspace_id=str(agent.workspace_id.value),
            name=agent.name,
            type=agent.type.value.value,
            status=agent.status.value.value,
            voice_config=AgentMapper.to_voice_dto(agent.voice_config),
            runtime_config=AgentMapper.to_runtime_dto(agent.runtime_config),
            llm_config=AgentMapper.to_llm_dto(agent.llm_config),
            memory_config=AgentMapper.to_memory_dto(agent.memory_config),
            playbook_id=str(agent.playbook_id.value) if agent.playbook_id else None,
            prompt_id=str(agent.prompt_id.value) if agent.prompt_id else None,
            tools=tuple(AgentMapper.to_tool_dto(t) for t in agent.tools),
            policies=tuple(AgentMapper.to_policy_dto(p) for p in agent.policies),
            version=agent.version,
            created_at=agent.created_at.value,
        )

    @staticmethod
    def to_voice_dto(config: AgentVoiceConfig) -> AgentVoiceConfigDTO:
        return AgentVoiceConfigDTO(
            tts_provider=config.tts_provider,
            voice_id=config.voice_id,
            speed=config.speed,
            pitch=config.pitch,
            language=config.language.code,
        )

    @staticmethod
    def to_runtime_dto(config: AgentRuntimeConfig) -> AgentRuntimeConfigDTO:
        return AgentRuntimeConfigDTO(
            max_concurrent_sessions=config.max_concurrent_sessions,
            session_timeout_seconds=config.session_timeout_seconds,
            silence_threshold_ms=config.silence_threshold_ms,
            barge_in_enabled=config.barge_in_enabled,
        )

    @staticmethod
    def to_llm_dto(config: AgentLLMConfig) -> AgentLLMConfigDTO:
        return AgentLLMConfigDTO(
            provider=config.provider,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            context_window=config.context_window,
        )

    @staticmethod
    def to_memory_dto(config: AgentMemoryConfig) -> AgentMemoryConfigDTO:
        return AgentMemoryConfigDTO(
            short_term_window_size=config.short_term_window_size,
            long_term_enabled=config.long_term_enabled,
            long_term_strategy=config.long_term_strategy,
        )

    @staticmethod
    def to_tool_dto(tool: AgentTool) -> AgentToolDTO:
        return AgentToolDTO(
            id=str(tool.id.value),
            name=tool.name,
            tool_type=tool.tool_type,
            schema=tool.schema,
            config=tool.config,
            enabled=tool.enabled,
        )

    @staticmethod
    def to_policy_dto(policy: AgentPolicy) -> AgentPolicyDTO:
        return AgentPolicyDTO(
            id=str(policy.id.value),
            policy_type=policy.policy_type,
            rule=policy.rule,
            violation_action=policy.violation_action,
            enforced=policy.enforced,
            priority=policy.priority,
        )
