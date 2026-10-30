"""
AgentFactory for Agent Bounded Context.

Encapsulates Agent aggregate root construction with sensible defaults per AgentType category.
"""

from __future__ import annotations

from shared.kernel.value_objects import AgentId, WorkspaceId

from agent.domain.entities.agent import Agent
from agent.domain.entities.agent_policy import AgentPolicy
from agent.domain.events.agent_created import AgentCreated
from agent.domain.value_objects.agent_llm_config import AgentLLMConfig
from agent.domain.value_objects.agent_memory_config import AgentMemoryConfig
from agent.domain.value_objects.agent_runtime_config import AgentRuntimeConfig
from agent.domain.value_objects.agent_status import AgentStatus
from agent.domain.value_objects.agent_type import AgentType
from agent.domain.value_objects.agent_voice_config import AgentVoiceConfig


class AgentFactory:
    """Factory for constructing new Agent Aggregate Roots."""

    @classmethod
    def create(
        self,
        workspace_id: WorkspaceId,
        name: str,
        agent_type: AgentType | None = None,
        agent_id: AgentId | None = None,
    ) -> Agent:
        """Create and initialize a new Agent aggregate root.

        Args:
            workspace_id: Owning WorkspaceId.
            name: Agent name.
            agent_type: Optional AgentType (defaults to SALES if None).
            agent_id: Optional explicit AgentId.

        Returns:
            Initialized Agent aggregate root with recorded AgentCreated domain event.
        """
        a_id = agent_id or AgentId()
        a_type = agent_type or AgentType.sales()

        # Defaults per type
        voice_cfg = AgentVoiceConfig.default()
        runtime_cfg = AgentRuntimeConfig.default()
        llm_cfg = AgentLLMConfig.default()
        memory_cfg = AgentMemoryConfig.default()

        default_policy = AgentPolicy.default_fallback()

        agent = Agent(
            id=a_id,
            workspace_id=workspace_id,
            name=name,
            type=a_type,
            status=AgentStatus.draft(),
            voice_config=voice_cfg,
            runtime_config=runtime_cfg,
            llm_config=llm_cfg,
            memory_config=memory_cfg,
            tools=(),
            policies=(default_policy,),
        )

        agent._raise_event(
            AgentCreated(
                agent_id=str(a_id.value),
                workspace_id=str(workspace_id.value),
                agent_name=name,
                agent_type=a_type.value.value,
            )
        )

        return agent
