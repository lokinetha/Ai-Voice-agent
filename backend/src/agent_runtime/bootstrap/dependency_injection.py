"""
Agent Runtime Dependency Injection Bootstrap Container.
"""

from __future__ import annotations

from voice.domain.ports.llm_runtime_port import LLMRuntimePort
from voice.infrastructure.adapters.fake_llm_runtime_adapter import (
    FakeLLMRuntimeAdapter,
)

from agent_runtime.application.commands.execute_agent_turn import (
    ExecuteAgentTurnHandler,
)
from agent_runtime.application.ports.agent_config_reader_port import (
    AgentConfigReaderPort,
)
from agent_runtime.application.ports.conversation_context_port import (
    ConversationContextPort,
)
from agent_runtime.application.ports.knowledge_retrieval_port import (
    KnowledgeRetrievalPort,
)
from agent_runtime.application.ports.published_prompt_reader_port import (
    PublishedPromptReaderPort,
)
from agent_runtime.application.services.agent_runtime_service import (
    AgentRuntimeService,
)
from agent_runtime.infrastructure.adapters.fake_agent_config_reader_adapter import (
    FakeAgentConfigReaderAdapter,
)
from agent_runtime.infrastructure.adapters.fake_conversation_context_adapter import (
    FakeConversationContextAdapter,
)
from agent_runtime.infrastructure.adapters.fake_knowledge_retrieval_adapter import (
    FakeKnowledgeRetrievalAdapter,
)
from agent_runtime.infrastructure.adapters.fake_published_prompt_reader_adapter import (
    FakePublishedPromptReaderAdapter,
)


class AgentRuntimeContainer:
    """Dependency injection container for Agent Runtime services and ports."""

    def __init__(
        self,
        agent_config_port: AgentConfigReaderPort | None = None,
        published_prompt_port: PublishedPromptReaderPort | None = None,
        conversation_context_port: ConversationContextPort | None = None,
        knowledge_retrieval_port: KnowledgeRetrievalPort | None = None,
        llm_runtime_port: LLMRuntimePort | None = None,
    ) -> None:
        self.agent_config_port = agent_config_port or FakeAgentConfigReaderAdapter()
        self.published_prompt_port = (
            published_prompt_port or FakePublishedPromptReaderAdapter()
        )
        self.conversation_context_port = (
            conversation_context_port or FakeConversationContextAdapter()
        )
        self.knowledge_retrieval_port = (
            knowledge_retrieval_port or FakeKnowledgeRetrievalAdapter()
        )
        self.llm_runtime_port = llm_runtime_port or FakeLLMRuntimeAdapter()

        self.runtime_service = AgentRuntimeService(
            agent_config_port=self.agent_config_port,
            published_prompt_port=self.published_prompt_port,
            conversation_context_port=self.conversation_context_port,
            knowledge_retrieval_port=self.knowledge_retrieval_port,
            llm_runtime_port=self.llm_runtime_port,
        )

    def get_execute_agent_turn_handler(self) -> ExecuteAgentTurnHandler:
        """Construct ExecuteAgentTurnHandler."""
        return ExecuteAgentTurnHandler(runtime_service=self.runtime_service)
