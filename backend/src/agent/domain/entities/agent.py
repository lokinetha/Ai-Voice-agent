"""
Agent Aggregate Root for Agent Bounded Context.

Central Aggregate Root managing agent Voice, LLM, Runtime, Memory configurations,
assigned Tools, Policies, Playbook references, Prompt references, and publishing state.
"""

from __future__ import annotations

from collections.abc import Sequence

from shared.kernel.aggregate_root import AggregateRoot
from shared.kernel.result import Error, Result
from shared.kernel.value_objects import (
    AgentId,
    EntityId,
    PlaybookId,
    PromptId,
    Timestamp,
    WorkspaceId,
)

from agent.domain.entities.agent_policy import AgentPolicy
from agent.domain.entities.agent_tool import AgentTool
from agent.domain.events.agent_archived import AgentArchived
from agent.domain.events.agent_cloned import AgentCloned
from agent.domain.events.agent_published import AgentPublished
from agent.domain.events.agent_unpublished import AgentUnpublished
from agent.domain.events.agent_updated import AgentUpdated
from agent.domain.value_objects.agent_llm_config import AgentLLMConfig
from agent.domain.value_objects.agent_memory_config import AgentMemoryConfig
from agent.domain.value_objects.agent_runtime_config import AgentRuntimeConfig
from agent.domain.value_objects.agent_status import AgentStatus
from agent.domain.value_objects.agent_type import AgentType
from agent.domain.value_objects.agent_voice_config import AgentVoiceConfig


class Agent(AggregateRoot[AgentId]):
    """Agent Aggregate Root.

    Enforces business logic and domain invariants for publishing and configuring AI Voice Agents.
    """

    def __init__(
        self,
        id: AgentId,
        workspace_id: WorkspaceId,
        name: str,
        type: AgentType,
        status: AgentStatus = AgentStatus.draft(),
        voice_config: AgentVoiceConfig | None = None,
        runtime_config: AgentRuntimeConfig | None = None,
        llm_config: AgentLLMConfig | None = None,
        memory_config: AgentMemoryConfig | None = None,
        playbook_id: PlaybookId | None = None,
        prompt_id: PromptId | None = None,
        tools: Sequence[AgentTool] = (),
        policies: Sequence[AgentPolicy] = (),
        created_at: Timestamp | None = None,
        version: int = 1,
    ) -> None:
        super().__init__(id=id, created_at=created_at, version=version)

        if not name or not isinstance(name, str) or not name.strip():
            raise ValueError("Agent name cannot be empty")

        self._workspace_id = workspace_id
        self._name = name.strip()
        self._type = type
        self._status = status

        self._voice_config = voice_config or AgentVoiceConfig.default()
        self._runtime_config = runtime_config or AgentRuntimeConfig.default()
        self._llm_config = llm_config or AgentLLMConfig.default()
        self._memory_config = memory_config or AgentMemoryConfig.default()

        self._playbook_id = playbook_id
        self._prompt_id = prompt_id

        self._tools: dict[EntityId, AgentTool] = {t.id: t for t in tools}
        self._policies: dict[EntityId, AgentPolicy] = {p.id: p for p in policies}

    @property
    def workspace_id(self) -> WorkspaceId:
        """Get owning workspace identifier."""
        return self._workspace_id

    @property
    def name(self) -> str:
        """Get agent name string."""
        return self._name

    @property
    def type(self) -> AgentType:
        """Get agent category/type value object."""
        return self._type

    @property
    def status(self) -> AgentStatus:
        """Get current agent status value object."""
        return self._status

    @property
    def voice_config(self) -> AgentVoiceConfig:
        """Get voice configuration value object."""
        return self._voice_config

    @property
    def runtime_config(self) -> AgentRuntimeConfig:
        """Get runtime execution configuration value object."""
        return self._runtime_config

    @property
    def llm_config(self) -> AgentLLMConfig:
        """Get LLM inference configuration value object."""
        return self._llm_config

    @property
    def memory_config(self) -> AgentMemoryConfig:
        """Get session memory configuration value object."""
        return self._memory_config

    @property
    def playbook_id(self) -> PlaybookId | None:
        """Get associated PlaybookId reference, if set."""
        return self._playbook_id

    @property
    def prompt_id(self) -> PromptId | None:
        """Get associated PromptId reference, if set."""
        return self._prompt_id

    @property
    def tools(self) -> tuple[AgentTool, ...]:
        """Get tuple of assigned AgentTool entities."""
        return tuple(self._tools.values())

    @property
    def policies(self) -> tuple[AgentPolicy, ...]:
        """Get tuple of assigned AgentPolicy entities."""
        return tuple(self._policies.values())

    def update_name(self, new_name: str) -> Result[None]:
        """Update agent name."""
        if not new_name or not isinstance(new_name, str) or not new_name.strip():
            return Result.fail(Error("VALIDATION_ERROR", "Agent name cannot be empty"))
        self._name = new_name.strip()
        self._raise_event(AgentUpdated(agent_id=str(self.id.value), workspace_id=str(self.workspace_id.value), updated_fields=("name",)))
        return Result.ok(None)

    def set_playbook_id(self, playbook_id: PlaybookId) -> None:
        """Associate Playbook ID reference."""
        self._playbook_id = playbook_id

    def set_prompt_id(self, prompt_id: PromptId) -> None:
        """Associate Prompt ID reference."""
        self._prompt_id = prompt_id

    def update_voice_config(self, config: AgentVoiceConfig) -> Result[None]:
        """Update Voice configuration."""
        self._voice_config = config
        self._raise_event(AgentUpdated(agent_id=str(self.id.value), workspace_id=str(self.workspace_id.value), updated_fields=("voice_config",)))
        return Result.ok(None)

    def update_llm_config(self, config: AgentLLMConfig) -> Result[None]:
        """Update LLM configuration."""
        self._llm_config = config
        self._raise_event(AgentUpdated(agent_id=str(self.id.value), workspace_id=str(self.workspace_id.value), updated_fields=("llm_config",)))
        return Result.ok(None)

    def update_runtime_config(self, config: AgentRuntimeConfig) -> Result[None]:
        """Update Runtime configuration."""
        self._runtime_config = config
        self._raise_event(AgentUpdated(agent_id=str(self.id.value), workspace_id=str(self.workspace_id.value), updated_fields=("runtime_config",)))
        return Result.ok(None)

    def update_memory_config(self, config: AgentMemoryConfig) -> Result[None]:
        """Update Memory configuration."""
        self._memory_config = config
        self._raise_event(AgentUpdated(agent_id=str(self.id.value), workspace_id=str(self.workspace_id.value), updated_fields=("memory_config",)))
        return Result.ok(None)

    def add_tool(self, tool: AgentTool) -> Result[None]:
        """Add tool entity to Agent."""
        self._tools[tool.id] = tool
        return Result.ok(None)

    def remove_tool(self, tool_id: EntityId) -> Result[None]:
        """Remove tool entity by ID."""
        if tool_id not in self._tools:
            return Result.fail(Error("NOT_FOUND", f"Tool {tool_id.value} not found"))
        del self._tools[tool_id]
        return Result.ok(None)

    def add_policy(self, policy: AgentPolicy) -> Result[None]:
        """Add policy entity to Agent."""
        self._policies[policy.id] = policy
        return Result.ok(None)

    def publish(self) -> Result[None]:
        """Publish Agent to make it ready for voice streaming."""
        if self._playbook_id is None or not self._playbook_id.value:
            return Result.fail(
                Error("PRECONDITION_FAILED", "Cannot publish Agent without an active Playbook")
            )

        if self._prompt_id is None or not self._prompt_id.value:
            return Result.fail(
                Error("PRECONDITION_FAILED", "Cannot publish Agent without an active Prompt")
            )

        if self._status == AgentStatus.archived():
            return Result.fail(
                Error("INVALID_STATE", "Cannot publish an archived Agent")
            )

        self._status = AgentStatus.published()
        self._version += 1

        self._raise_event(
            AgentPublished(
                agent_id=str(self.id.value),
                workspace_id=str(self.workspace_id.value),
                playbook_id=str(self._playbook_id.value),
                prompt_id=str(self._prompt_id.value),
                version=self._version,
            )
        )
        return Result.ok(None)

    def unpublish(self, reason: str = "user_paused") -> Result[None]:
        """Pause or unpublish Agent."""
        if not self._status.is_published:
            return Result.ok(None)

        self._status = AgentStatus.paused()
        self._raise_event(
            AgentUnpublished(
                agent_id=str(self.id.value),
                workspace_id=str(self.workspace_id.value),
                reason=reason,
            )
        )
        return Result.ok(None)

    def archive(self) -> Result[None]:
        """Archive Agent aggregate."""
        if self._status.is_archived:
            return Result.ok(None)

        self._status = AgentStatus.archived()
        self._raise_event(
            AgentArchived(
                agent_id=str(self.id.value),
                workspace_id=str(self.workspace_id.value),
            )
        )
        return Result.ok(None)

    def clone(self, new_name: str, new_agent_id: AgentId | None = None) -> Result[Agent]:
        """Clone existing Agent aggregate with new name."""
        cloned_id = new_agent_id or AgentId()

        cloned_tools = [
            AgentTool(
                id=EntityId(),
                name=t.name,
                tool_type=t.tool_type,
                schema=t.schema,
                config=t.config,
                enabled=t.enabled,
            )
            for t in self.tools
        ]

        cloned_policies = [
            AgentPolicy(
                id=EntityId(),
                policy_type=p.policy_type,
                rule=p.rule,
                violation_action=p.violation_action,
                enforced=p.enforced,
                priority=p.priority,
            )
            for p in self.policies
        ]

        cloned_agent = Agent(
            id=cloned_id,
            workspace_id=self.workspace_id,
            name=new_name,
            type=self.type,
            status=AgentStatus.draft(),
            voice_config=self.voice_config,
            runtime_config=self.runtime_config,
            llm_config=self.llm_config,
            memory_config=self.memory_config,
            playbook_id=self.playbook_id,
            prompt_id=self.prompt_id,
            tools=cloned_tools,
            policies=cloned_policies,
        )

        cloned_agent._raise_event(
            AgentCloned(
                source_agent_id=str(self.id.value),
                new_agent_id=str(cloned_id.value),
                workspace_id=str(self.workspace_id.value),
                new_agent_name=new_name,
            )
        )

        return Result.ok(cloned_agent)
