"""
LLMRuntimePort Interface for Voice Bounded Context.

Abstract port for generating AI Agent responses from compiled runtime configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMRuntimePort(ABC):
    """Abstract port for generating conversational agent response text."""

    @abstractmethod
    async def generate_response(
        self,
        workspace_id: str,
        agent_id: str,
        conversation_id: str,
        prompt_text: str,
        compiled_prompt: str = "",
        conversation_context: list[dict[str, str]] | None = None,
        runtime_config: dict[str, Any] | None = None,
        knowledge_context: list[str] | None = None,
        tool_definitions: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Generate AI agent text response.

        Args:
            workspace_id: Owning Workspace ID.
            agent_id: Target Agent ID.
            conversation_id: Active Conversation ID.
            prompt_text: Input message/prompt text.
            compiled_prompt: Optional system instruction prompt string.
            conversation_context: Optional history of turns [{'role': 'user'|'assistant', 'content': '...'}].
            runtime_config: Optional generation parameters (temperature, top_p, max_output_tokens).
            knowledge_context: Optional snippets of retrieved knowledge.
            tool_definitions: Optional tool/function definitions.

        Returns:
            Generated response text string or LLMResponseDTO object.
        """
        ...
