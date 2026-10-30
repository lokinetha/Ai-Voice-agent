"""
Unit tests for AgentRuntimeService orchestration module.

Tests successful turn execution, missing prompt, missing agent, LLM timeout,
knowledge retrieval failure (graceful degradation), correlation ID propagation,
and conversation response persistence.
"""

from __future__ import annotations

import asyncio
import unittest

from agent_runtime.application.commands.execute_agent_turn import (
    ExecuteAgentTurnCommand,
    ExecuteAgentTurnHandler,
)
from agent_runtime.application.dto.agent_runtime_dto import (
    AgentConfigDTO,
    ConversationTurnDTO,
    PublishedPromptDTO,
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
from voice.infrastructure.adapters.fake_llm_runtime_adapter import (
    FakeLLMRuntimeAdapter,
)
from voice.infrastructure.adapters.gemini_llm_adapter import LLMTimeoutError


class TimeoutLLMRuntimeAdapter(FakeLLMRuntimeAdapter):
    """Test double simulating LLM timeout exception."""

    async def generate_response(self, *args: object, **kwargs: object) -> str:
        raise LLMTimeoutError("Gemini API request timed out after 30.0s")


class TestAgentRuntimeService(unittest.TestCase):
    """Unit test suite for AgentRuntimeService."""

    def setUp(self) -> None:
        self.workspace_id = "ws-test-1"
        self.agent_id = "agent-test-1"
        self.conversation_id = "conv-test-1"

        self.agent_config = AgentConfigDTO(
            agent_id=self.agent_id,
            workspace_id=self.workspace_id,
            name="Sales Assistant",
            is_active=True,
            model_name="gemini-2.5-flash",
            temperature=0.7,
        )

        self.published_prompt = PublishedPromptDTO(
            prompt_id="prompt-test-1",
            agent_id=self.agent_id,
            workspace_id=self.workspace_id,
            version=1,
            compiled_template="You are a helpful customer sales AI assistant.",
            is_published=True,
        )

        self.agent_config_port = FakeAgentConfigReaderAdapter([self.agent_config])
        self.published_prompt_port = FakePublishedPromptReaderAdapter([self.published_prompt])
        self.conv_context_port = FakeConversationContextAdapter()
        self.knowledge_port = FakeKnowledgeRetrievalAdapter(["Pricing is $10/mo."])
        self.llm_runtime_port = FakeLLMRuntimeAdapter()

        self.service = AgentRuntimeService(
            agent_config_port=self.agent_config_port,
            published_prompt_port=self.published_prompt_port,
            conversation_context_port=self.conv_context_port,
            knowledge_retrieval_port=self.knowledge_port,
            llm_runtime_port=self.llm_runtime_port,
        )

    def test_successful_agent_turn_execution(self) -> None:
        async def run() -> None:
            # Seed conversation history
            self.conv_context_port.seed_history(
                self.conversation_id,
                [
                    ConversationTurnDTO("msg-1", "CUSTOMER", "Hello"),
                    ConversationTurnDTO("msg-2", "AGENT", "Hello! How can I help?"),
                ],
            )

            res = await self.service.execute_turn(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                message_text="What is your pricing?",
            )

            self.assertTrue(res.is_success)
            resp = res.value
            self.assertIn("pricing", resp.content.lower())
            self.assertEqual(resp.agent_id, self.agent_id)
            self.assertEqual(resp.conversation_id, self.conversation_id)
            self.assertEqual(resp.workspace_id, self.workspace_id)

            # Verify conversation response persistence
            history = await self.conv_context_port.get_conversation_history(self.conversation_id)
            self.assertEqual(len(history), 3)
            self.assertEqual(history[-1].role, "AGENT")
            self.assertEqual(history[-1].content, resp.content)

        asyncio.run(run())

    def test_missing_agent_failure(self) -> None:
        async def run() -> None:
            res = await self.service.execute_turn(
                workspace_id=self.workspace_id,
                agent_id="non-existent-agent",
                conversation_id=self.conversation_id,
                message_text="Hello",
            )

            self.assertTrue(res.is_failure)
            self.assertEqual(res.error.code, "AGENT_NOT_FOUND")

        asyncio.run(run())

    def test_missing_published_prompt_failure(self) -> None:
        async def run() -> None:
            # Agent exists without published prompt
            no_prompt_agent = AgentConfigDTO(
                agent_id="ag-no-prompt",
                workspace_id=self.workspace_id,
                name="Draft Agent",
            )
            self.agent_config_port.add_config(no_prompt_agent)

            res = await self.service.execute_turn(
                workspace_id=self.workspace_id,
                agent_id="ag-no-prompt",
                conversation_id=self.conversation_id,
                message_text="Hello",
            )

            self.assertTrue(res.is_failure)
            self.assertEqual(res.error.code, "PROMPT_NOT_PUBLISHED")

        asyncio.run(run())

    def test_llm_timeout_failure(self) -> None:
        async def run() -> None:
            timeout_service = AgentRuntimeService(
                agent_config_port=self.agent_config_port,
                published_prompt_port=self.published_prompt_port,
                conversation_context_port=self.conv_context_port,
                knowledge_retrieval_port=self.knowledge_port,
                llm_runtime_port=TimeoutLLMRuntimeAdapter(),
            )

            res = await timeout_service.execute_turn(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                message_text="Slow request",
            )

            self.assertTrue(res.is_failure)
            self.assertEqual(res.error.code, "LLM_TIMEOUT")

        asyncio.run(run())

    def test_knowledge_retrieval_failure_graceful_degradation(self) -> None:
        async def run() -> None:
            # Knowledge port throws exception
            failing_knowledge_port = FakeKnowledgeRetrievalAdapter(should_fail=True)
            resilient_service = AgentRuntimeService(
                agent_config_port=self.agent_config_port,
                published_prompt_port=self.published_prompt_port,
                conversation_context_port=self.conv_context_port,
                knowledge_retrieval_port=failing_knowledge_port,
                llm_runtime_port=self.llm_runtime_port,
            )

            res = await resilient_service.execute_turn(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                message_text="Hello resilient turn",
            )

            # Turn MUST succeed despite knowledge retrieval failure
            self.assertTrue(res.is_success)
            self.assertIsNotNone(res.value.content)

            # Conversation history MUST be persisted cleanly
            history = await self.conv_context_port.get_conversation_history(self.conversation_id)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0].role, "AGENT")

        asyncio.run(run())

    def test_correlation_id_propagation(self) -> None:
        async def run() -> None:
            custom_corr_id = "custom-correlation-trace-999"
            res = await self.service.execute_turn(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                message_text="Trace test",
                correlation_id=custom_corr_id,
            )

            self.assertTrue(res.is_success)
            self.assertEqual(res.value.correlation_id, custom_corr_id)

        asyncio.run(run())

    def test_execute_agent_turn_command_handler(self) -> None:
        async def run() -> None:
            handler = ExecuteAgentTurnHandler(runtime_service=self.service)
            cmd = ExecuteAgentTurnCommand(
                workspace_id=self.workspace_id,
                agent_id=self.agent_id,
                conversation_id=self.conversation_id,
                message_text="Command handler test",
            )

            res = await handler.handle(cmd)
            self.assertTrue(res.is_success)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
