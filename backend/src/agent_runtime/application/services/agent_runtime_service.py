"""
AgentRuntimeService Application Orchestrator for Agent Runtime.

Orchestrates Agent + Published Prompt + Conversation + Knowledge + Gemini LLM Runtime
to generate conversational AI Agent responses cleanly through application ports.
"""

from __future__ import annotations

import logging
from typing import Any

from shared.kernel.result import Error, Result
from voice.domain.ports.llm_runtime_port import LLMRuntimePort
from voice.infrastructure.adapters.gemini_llm_adapter import (
    LLMProviderError,
    LLMTimeoutError,
)

from agent_runtime.application.dto.agent_runtime_dto import AgentResponse
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

logger = logging.getLogger(__name__)


class AgentRuntimeService:
    """Application-level Orchestrator coordinating cross-context Agent execution."""

    def __init__(
        self,
        agent_config_port: AgentConfigReaderPort,
        published_prompt_port: PublishedPromptReaderPort,
        conversation_context_port: ConversationContextPort,
        knowledge_retrieval_port: KnowledgeRetrievalPort,
        llm_runtime_port: LLMRuntimePort,
    ) -> None:
        """Initialize AgentRuntimeService with required application ports."""
        self._agent_config_port = agent_config_port
        self._published_prompt_port = published_prompt_port
        self._conv_context_port = conversation_context_port
        self._knowledge_port = knowledge_retrieval_port
        self._llm_runtime_port = llm_runtime_port

    async def execute_turn(
        self,
        workspace_id: str,
        agent_id: str,
        conversation_id: str,
        message_text: str,
        correlation_id: str | None = None,
        language: str | None = None,
    ) -> Result[AgentResponse]:
        """Execute single agent conversational turn orchestration flow."""
        if not workspace_id or not agent_id or not conversation_id:
            return Result.fail(
                Error("VALIDATION_ERROR", "workspace_id, agent_id, and conversation_id required")
            )

        corr_id = correlation_id or f"{workspace_id}:{conversation_id}"

        # 1. Load active Agent configuration
        agent_config = await self._agent_config_port.get_agent_config(
            workspace_id=workspace_id, agent_id=agent_id
        )
        if agent_config is None or not agent_config.is_active:
            return Result.fail(
                Error("AGENT_NOT_FOUND", f"Agent '{agent_id}' not found or inactive")
            )

        # 2. Load published Prompt version
        published_prompt = await self._published_prompt_port.get_published_prompt(
            workspace_id=workspace_id, agent_id=agent_id
        )
        if published_prompt is None or not published_prompt.is_published:
            return Result.fail(
                Error("PROMPT_NOT_PUBLISHED", f"Published prompt for agent '{agent_id}' not found")
            )

        # 3. Fetch Conversation context history (prior turns)
        history_turns = await self._conv_context_port.get_conversation_history(conversation_id)
        conv_context: list[dict[str, str]] = []
        for t in history_turns:
            if (
                history_turns
                and t == history_turns[-1]
                and t.role in ("CUSTOMER", "customer", "user")
                and t.content == message_text
            ):
                continue
            conv_context.append({"role": t.role, "content": t.content})

        # 4. Retrieve Knowledge context (graceful error handling)
        knowledge_snippets: list[str] = []
        try:
            knowledge_snippets = await self._knowledge_port.retrieve_knowledge(
                workspace_id=workspace_id, query=message_text
            )
        except Exception as exc:
            logger.warning(
                "Knowledge retrieval failed during agent turn execution: %s", exc
            )
            knowledge_snippets = []

        # 5. Build runtime parameters & call LLMRuntimePort
        runtime_config: dict[str, Any] = {
            "temperature": agent_config.temperature,
            "max_output_tokens": agent_config.max_output_tokens,
            "model_name": agent_config.model_name,
        }

        compiled_prompt = published_prompt.compiled_template
        if language:
            runtime_config["language"] = language
            norm_lang = language.strip().lower()
            if norm_lang.startswith("te"):
                lang_inst = "\n\n[System Instruction: Respond ONLY in Telugu (తెలుగు). Use Telugu script. Do not respond in English.]"
            elif norm_lang.startswith("en"):
                lang_inst = "\n\n[System Instruction: Respond in English.]"
            else:
                lang_inst = f"\n\n[System Instruction: Respond ONLY in {language}. Use native script. Do not respond in English.]"
            compiled_prompt += lang_inst

        try:
            llm_result = await self._llm_runtime_port.generate_response(
                workspace_id=workspace_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                prompt_text=message_text,
                compiled_prompt=compiled_prompt,
                conversation_context=conv_context,
                runtime_config=runtime_config,
                knowledge_context=knowledge_snippets,
            )
        except LLMTimeoutError as err:
            return Result.fail(Error("LLM_TIMEOUT", str(err)))
        except LLMProviderError as err:
            return Result.fail(Error("LLM_PROVIDER_ERROR", str(err)))
        except Exception as err:
            return Result.fail(Error("LLM_PROVIDER_ERROR", f"LLM execution failed: {err}"))

        # Extract content & metadata from result object
        content_text = getattr(llm_result, "content", str(llm_result))
        finish_reason = str(getattr(llm_result, "finish_reason", "STOP"))
        prompt_tokens = int(getattr(llm_result, "prompt_tokens", 0))
        candidate_tokens = int(getattr(llm_result, "candidate_tokens", 0))
        total_tokens = int(getattr(llm_result, "total_tokens", prompt_tokens + candidate_tokens))
        latency_ms = float(getattr(llm_result, "latency_ms", 0.0))
        model_used = str(getattr(llm_result, "model", agent_config.model_name))

        # 6. Record generated agent message in Conversation context
        await self._conv_context_port.append_message(
            conversation_id=conversation_id,
            role="AGENT",
            content=content_text,
        )

        # 7. Construct & return AgentResponse
        agent_response = AgentResponse(
            content=content_text,
            agent_id=agent_id,
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            correlation_id=corr_id,
            model_name=model_used,
            finish_reason=finish_reason,
            prompt_tokens=prompt_tokens,
            candidate_tokens=candidate_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
        )

        return Result.ok(agent_response)
