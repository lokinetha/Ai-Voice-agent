"""
FakeLLMRuntimeAdapter implementing LLMRuntimePort.

Provider-independent fake LLM agent runtime adapter.
"""

from __future__ import annotations

from typing import Any

from voice.domain.ports.llm_runtime_port import LLMRuntimePort


class FakeLLMRuntimeAdapter(LLMRuntimePort):
    """Fake LLM agent runtime adapter."""

    def __init__(self, override_response: str | None = None) -> None:
        self._override_response = override_response

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
    ) -> str:
        """Generate deterministic response for input prompt without vendor API calls."""
        if self._override_response is not None:
            return self._override_response

        lang = (runtime_config or {}).get("language", "")
        if "te" in lang.lower() or "telugu" in compiled_prompt.lower():
            return "నమస్కారం! నేను మీకు ఎలా సహాయపడగలను?"

        if "cost" in prompt_text.lower() or "price" in prompt_text.lower():
            return "Our pricing is transparent and scalable for your workspace needs."
        if "hello" in prompt_text.lower() or "hi" in prompt_text.lower():
            return "Hello! How can I assist you today?"
        return f"Thank you for your message: '{prompt_text}'. I am here to help you."
