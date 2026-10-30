"""
SQLAlchemy 2.x Repository Implementation for Agent Aggregate Root.

Implements AgentRepository domain interface using async SQLAlchemy sessions.
"""

from __future__ import annotations

from datetime import UTC

from shared.kernel.specification import Specification
from shared.kernel.value_objects import (
    AgentId,
    EntityId,
    Language,
    PlaybookId,
    PromptId,
    Timestamp,
    WorkspaceId,
)
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.domain.entities.agent import Agent
from agent.domain.entities.agent_policy import AgentPolicy
from agent.domain.entities.agent_tool import AgentTool
from agent.domain.repositories.agent_repository import AgentRepository
from agent.domain.value_objects.agent_llm_config import AgentLLMConfig
from agent.domain.value_objects.agent_memory_config import AgentMemoryConfig
from agent.domain.value_objects.agent_runtime_config import AgentRuntimeConfig
from agent.domain.value_objects.agent_status import AgentStatus, AgentStatusType
from agent.domain.value_objects.agent_type import AgentCategory, AgentType
from agent.domain.value_objects.agent_voice_config import AgentVoiceConfig
from agent.infrastructure.persistence.models import (
    AgentLLMConfigModel,
    AgentMemoryConfigModel,
    AgentModel,
    AgentPolicyModel,
    AgentRuntimeConfigModel,
    AgentToolModel,
    AgentVoiceConfigModel,
)


class SqlAlchemyAgentRepository(AgentRepository):
    """SQLAlchemy implementation of AgentRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: AgentId) -> Agent | None:
        """Retrieve Agent aggregate by ID."""
        stmt = select(AgentModel).where(AgentModel.id == str(id.value))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def get_by_workspace_and_name(
        self, workspace_id: WorkspaceId, name: str
    ) -> Agent | None:
        """Find Agent by workspace ID and name string."""
        stmt = select(AgentModel).where(
            AgentModel.workspace_id == str(workspace_id.value),
            AgentModel.name == name.strip(),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_aggregate(model)

    async def find_by_workspace(self, workspace_id: WorkspaceId) -> list[Agent]:
        """Find all Agents belonging to target WorkspaceId."""
        stmt = select(AgentModel).where(AgentModel.workspace_id == str(workspace_id.value))
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_aggregate(m) for m in models]

    async def save(self, aggregate: Agent) -> None:
        """Persist or update Agent aggregate root and all configurations, tools, policies."""
        stmt = select(AgentModel).where(AgentModel.id == str(aggregate.id.value))
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            model = AgentModel(
                id=str(aggregate.id.value),
                workspace_id=str(aggregate.workspace_id.value),
                name=aggregate.name,
                type=aggregate.type.value.value,
                status=aggregate.status.value.value,
                playbook_id=str(aggregate.playbook_id.value) if aggregate.playbook_id else None,
                prompt_id=str(aggregate.prompt_id.value) if aggregate.prompt_id else None,
                version=aggregate.version,
                created_at=aggregate.created_at.value,
                voice_config=AgentVoiceConfigModel(
                    agent_id=str(aggregate.id.value),
                    tts_provider=aggregate.voice_config.tts_provider,
                    voice_id=aggregate.voice_config.voice_id,
                    speed=aggregate.voice_config.speed,
                    pitch=aggregate.voice_config.pitch,
                    language=aggregate.voice_config.language.code,
                ),
                runtime_config=AgentRuntimeConfigModel(
                    agent_id=str(aggregate.id.value),
                    max_concurrent_sessions=aggregate.runtime_config.max_concurrent_sessions,
                    session_timeout_seconds=aggregate.runtime_config.session_timeout_seconds,
                    silence_threshold_ms=aggregate.runtime_config.silence_threshold_ms,
                    barge_in_enabled=aggregate.runtime_config.barge_in_enabled,
                ),
                llm_config=AgentLLMConfigModel(
                    agent_id=str(aggregate.id.value),
                    provider=aggregate.llm_config.provider,
                    model=aggregate.llm_config.model,
                    temperature=aggregate.llm_config.temperature,
                    max_tokens=aggregate.llm_config.max_tokens,
                    context_window=aggregate.llm_config.context_window,
                ),
                memory_config=AgentMemoryConfigModel(
                    agent_id=str(aggregate.id.value),
                    short_term_window_size=aggregate.memory_config.short_term_window_size,
                    long_term_enabled=aggregate.memory_config.long_term_enabled,
                    long_term_strategy=aggregate.memory_config.long_term_strategy,
                ),
                tools=[
                    AgentToolModel(
                        id=str(t.id.value),
                        agent_id=str(aggregate.id.value),
                        name=t.name,
                        tool_type=t.tool_type,
                        schema_json=t.schema,
                        config_json=t.config,
                        enabled=t.enabled,
                    )
                    for t in aggregate.tools
                ],
                policies=[
                    AgentPolicyModel(
                        id=str(p.id.value),
                        agent_id=str(aggregate.id.value),
                        policy_type=p.policy_type,
                        rule=p.rule,
                        violation_action=p.violation_action,
                        enforced=p.enforced,
                        priority=p.priority,
                    )
                    for p in aggregate.policies
                ],
            )
            self._session.add(model)
        else:
            existing.name = aggregate.name
            existing.type = aggregate.type.value.value
            existing.status = aggregate.status.value.value
            existing.playbook_id = str(aggregate.playbook_id.value) if aggregate.playbook_id else None
            existing.prompt_id = str(aggregate.prompt_id.value) if aggregate.prompt_id else None
            existing.version = aggregate.version

            # Update embedded voice config
            if existing.voice_config:
                existing.voice_config.tts_provider = aggregate.voice_config.tts_provider
                existing.voice_config.voice_id = aggregate.voice_config.voice_id
                existing.voice_config.speed = aggregate.voice_config.speed
                existing.voice_config.pitch = aggregate.voice_config.pitch
                existing.voice_config.language = aggregate.voice_config.language.code

            # Update embedded llm config
            if existing.llm_config:
                existing.llm_config.provider = aggregate.llm_config.provider
                existing.llm_config.model = aggregate.llm_config.model
                existing.llm_config.temperature = aggregate.llm_config.temperature
                existing.llm_config.max_tokens = aggregate.llm_config.max_tokens
                existing.llm_config.context_window = aggregate.llm_config.context_window

    async def delete(self, aggregate: Agent) -> None:
        """Delete Agent aggregate from persistence."""
        stmt = sql_delete(AgentModel).where(AgentModel.id == str(aggregate.id.value))
        await self._session.execute(stmt)

    async def find(self, spec: Specification[Agent]) -> list[Agent]:
        """Find Agent aggregates satisfying specification filter."""
        stmt = select(AgentModel)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        aggregates = [self._to_aggregate(m) for m in models]
        return [a for a in aggregates if spec.is_satisfied_by(a)]

    async def count(self, spec: Specification[Agent]) -> int:
        """Count Agent aggregates satisfying specification filter."""
        aggregates = await self.find(spec)
        return len(aggregates)

    @staticmethod
    def _to_aggregate(model: AgentModel) -> Agent:
        """Map ORM AgentModel to domain Agent aggregate root."""
        created_at_dt = model.created_at
        if created_at_dt and created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=UTC)

        voice_cfg = (
            AgentVoiceConfig(
                tts_provider=model.voice_config.tts_provider,
                voice_id=model.voice_config.voice_id,
                speed=model.voice_config.speed,
                pitch=model.voice_config.pitch,
                language=Language(model.voice_config.language),
            )
            if model.voice_config
            else AgentVoiceConfig.default()
        )

        runtime_cfg = (
            AgentRuntimeConfig(
                max_concurrent_sessions=model.runtime_config.max_concurrent_sessions,
                session_timeout_seconds=model.runtime_config.session_timeout_seconds,
                silence_threshold_ms=model.runtime_config.silence_threshold_ms,
                barge_in_enabled=model.runtime_config.barge_in_enabled,
            )
            if model.runtime_config
            else AgentRuntimeConfig.default()
        )

        llm_cfg = (
            AgentLLMConfig(
                provider=model.llm_config.provider,
                model=model.llm_config.model,
                temperature=model.llm_config.temperature,
                max_tokens=model.llm_config.max_tokens,
                context_window=model.llm_config.context_window,
            )
            if model.llm_config
            else AgentLLMConfig.default()
        )

        memory_cfg = (
            AgentMemoryConfig(
                short_term_window_size=model.memory_config.short_term_window_size,
                long_term_enabled=model.memory_config.long_term_enabled,
                long_term_strategy=model.memory_config.long_term_strategy,
            )
            if model.memory_config
            else AgentMemoryConfig.default()
        )

        tools = [
            AgentTool(
                id=EntityId(t.id),
                name=t.name,
                tool_type=t.tool_type,
                schema=t.schema_json,
                config=t.config_json,
                enabled=t.enabled,
            )
            for t in model.tools
        ]

        policies = [
            AgentPolicy(
                id=EntityId(p.id),
                policy_type=p.policy_type,
                rule=p.rule,
                violation_action=p.violation_action,
                enforced=p.enforced,
                priority=p.priority,
            )
            for p in model.policies
        ]

        return Agent(
            id=AgentId(model.id),
            workspace_id=WorkspaceId(model.workspace_id),
            name=model.name,
            type=AgentType(AgentCategory(model.type)),
            status=AgentStatus(AgentStatusType(model.status)),
            voice_config=voice_cfg,
            runtime_config=runtime_cfg,
            llm_config=llm_cfg,
            memory_config=memory_cfg,
            playbook_id=PlaybookId(model.playbook_id) if model.playbook_id else None,
            prompt_id=PromptId(model.prompt_id) if model.prompt_id else None,
            tools=tools,
            policies=policies,
            created_at=Timestamp(created_at_dt),
            version=model.version,
        )
