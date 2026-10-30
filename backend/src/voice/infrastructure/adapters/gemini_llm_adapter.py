"""
Production Gemini Adapter implementing LLMRuntimePort for Voice Bounded Context.

Uses Google's official Gemini Python SDK with env configuration, controlled retries,
exponential backoff, error mapping, timeout handling, and secret sanitization.
"""

from __future__ import annotations

import asyncio
import os
import time
from collections.abc import AsyncGenerator
from typing import Any

from voice.domain.ports.llm_runtime_port import LLMRuntimePort
from voice.infrastructure.adapters.llm_dto import LLMResponseDTO


class LLMProviderError(Exception):
    """Controlled exception for LLM provider errors with sanitized error messages."""

    def __init__(self, message: str, code: str = "LLM_PROVIDER_ERROR") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class LLMTimeoutError(LLMProviderError):
    """Controlled exception for LLM provider timeouts."""

    def __init__(self, message: str = "LLM generation timed out") -> None:
        super().__init__(message=message, code="LLM_TIMEOUT")


class GeminiLLMAdapter(LLMRuntimePort):
    """Production Gemini adapter implementing LLMRuntimePort."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        client: Any | None = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        retry_delay_seconds: float = 0.5,
    ) -> None:
        """Initialize Gemini adapter."""
        self._api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self._model_name = (
            model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        )
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds
        self._client = client

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_client(self) -> Any:
        """Retrieve or lazily initialize the Gemini client."""
        if self._client is not None:
            return self._client

        if not self._api_key:
            raise LLMProviderError(
                "GEMINI_API_KEY environment variable or api_key parameter is required"
            )

        try:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
            return self._client
        except ImportError:
            try:
                import google.generativeai as legacy_genai

                legacy_genai.configure(api_key=self._api_key)
                self._client = legacy_genai.GenerativeModel(self._model_name)
                return self._client
            except ImportError as exc:
                raise LLMProviderError("Google GenAI Python SDK is not installed") from exc

    def _mask_secrets(self, text: str) -> str:
        """Sanitize text ensuring raw API keys are never leaked in logs or error messages."""
        if self._api_key and len(self._api_key) > 6:
            key_suffix = self._api_key[-4:]
            masked = f"***{key_suffix}"
            text = text.replace(self._api_key, masked)
        return text

    def _build_contents(
        self,
        prompt_text: str,
        conversation_context: list[dict[str, str]] | None = None,
    ) -> list[dict[str, Any]]:
        """Build Gemini-compatible content turns list."""
        contents: list[dict[str, Any]] = []

        if conversation_context:
            for turn in conversation_context:
                role = turn.get("role", "user")
                gemini_role = "model" if role in ("assistant", "agent", "model") else "user"
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": turn.get("content", "")}],
                })

        contents.append({
            "role": "user",
            "parts": [{"text": prompt_text}],
        })

        return contents

    def _build_system_instruction(
        self,
        compiled_prompt: str = "",
        knowledge_context: list[str] | None = None,
    ) -> str:
        """Build combined system instruction string."""
        instruction = compiled_prompt.strip()
        if knowledge_context:
            knowledge_text = "\n".join(f"- {item}" for item in knowledge_context)
            if instruction:
                instruction += f"\n\n=== KNOWLEDGE CONTEXT ===\n{knowledge_text}"
            else:
                instruction = f"=== KNOWLEDGE CONTEXT ===\n{knowledge_text}"
        return instruction

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
    ) -> LLMResponseDTO:
        """Generate AI Agent response with retry, backoff, and timeout handling."""
        correlation_id = f"{workspace_id}:{conversation_id}" if workspace_id else conversation_id
        start_time = time.time()

        attempt = 0
        last_exception: Exception | None = None

        while attempt <= self._max_retries:
            attempt += 1
            try:
                response_dto = await asyncio.wait_for(
                    self._execute_generation(
                        prompt_text=prompt_text,
                        compiled_prompt=compiled_prompt,
                        conversation_context=conversation_context,
                        runtime_config=runtime_config,
                        knowledge_context=knowledge_context,
                        tool_definitions=tool_definitions,
                        correlation_id=correlation_id,
                        start_time=start_time,
                    ),
                    timeout=self._timeout_seconds,
                )
                return response_dto

            except TimeoutError:
                last_exception = LLMTimeoutError(
                    f"Gemini API request timed out after {self._timeout_seconds}s"
                )
            except Exception as exc:
                sanitized_msg = self._mask_secrets(str(exc))
                is_retryable = (
                    "429" in sanitized_msg
                    or "500" in sanitized_msg
                    or "503" in sanitized_msg
                    or "rate limit" in sanitized_msg.lower()
                    or "quota" in sanitized_msg.lower()
                )
                last_exception = LLMProviderError(sanitized_msg)

                if not is_retryable or attempt > self._max_retries:
                    raise last_exception from exc

            if attempt <= self._max_retries:
                delay = self._retry_delay_seconds * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        if last_exception:
            raise last_exception
        raise LLMProviderError("Gemini generation failed")

    async def generate_response_stream(
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
    ) -> AsyncGenerator[str]:
        """Stream AI Agent response chunks using Gemini API."""
        client = self._get_client()
        contents = self._build_contents(prompt_text, conversation_context)
        system_instruction = self._build_system_instruction(compiled_prompt, knowledge_context)

        try:
            if hasattr(client, "aio") and hasattr(client.aio.models, "generate_content_stream"):
                try:
                    from google.genai import types

                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction if system_instruction else None,
                    )
                except ImportError:
                    config = None

                gen_args: dict[str, Any] = {
                    "model": self._model_name,
                    "contents": contents,
                }
                if config is not None:
                    gen_args["config"] = config

                stream = await client.aio.models.generate_content_stream(**gen_args)
                async for chunk in stream:
                    text_part = getattr(chunk, "text", str(chunk))
                    if text_part:
                        yield text_part
            else:
                resp_dto = await self.generate_response(
                    workspace_id=workspace_id,
                    agent_id=agent_id,
                    conversation_id=conversation_id,
                    prompt_text=prompt_text,
                    compiled_prompt=compiled_prompt,
                    conversation_context=conversation_context,
                    runtime_config=runtime_config,
                    knowledge_context=knowledge_context,
                    tool_definitions=tool_definitions,
                )
                yield resp_dto.content
        except Exception as exc:
            raise LLMProviderError(self._mask_secrets(str(exc))) from exc

    async def _execute_generation(
        self,
        prompt_text: str,
        compiled_prompt: str,
        conversation_context: list[dict[str, str]] | None,
        runtime_config: dict[str, Any] | None,
        knowledge_context: list[str] | None,
        tool_definitions: list[dict[str, Any]] | None,
        correlation_id: str,
        start_time: float,
    ) -> LLMResponseDTO:
        """Internal execution helper for Gemini API invocation."""
        client = self._get_client()
        contents = self._build_contents(prompt_text, conversation_context)
        system_instruction = self._build_system_instruction(compiled_prompt, knowledge_context)

        # Handle async vs sync client methods
        if hasattr(client, "aio") and hasattr(client.aio.models, "generate_content"):
            gen_args: dict[str, Any] = {
                "model": self._model_name,
                "contents": contents,
            }
            try:
                from google.genai import types

                if system_instruction:
                    gen_args["config"] = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                    )
            except ImportError:
                pass

            raw_resp = await client.aio.models.generate_content(**gen_args)
        elif hasattr(client, "generate_content"):
            func = client.generate_content
            if asyncio.iscoroutinefunction(func):
                raw_resp = await func(
                    contents=contents,
                    model=self._model_name,
                    system_instruction=system_instruction,
                )
            else:
                raw_resp = func(
                    contents=contents,
                    model=self._model_name,
                    system_instruction=system_instruction,
                )
        elif hasattr(client, "models") and hasattr(client.models, "generate_content"):
            gen_args = {
                "model": self._model_name,
                "contents": contents,
            }
            try:
                from google.genai import types

                if system_instruction:
                    gen_args["config"] = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                    )
            except ImportError:
                pass

            func = client.models.generate_content
            if asyncio.iscoroutinefunction(func):
                raw_resp = await func(**gen_args)
            else:
                raw_resp = func(**gen_args)
        elif callable(client):
            if asyncio.iscoroutinefunction(client):
                raw_resp = await client(prompt_text)
            else:
                raw_resp = client(prompt_text)
        else:
            raise LLMProviderError("Invalid Gemini client configuration")

        latency_ms = round((time.time() - start_time) * 1000, 2)

        content_text = ""
        finish_reason = "STOP"
        prompt_tokens = 0
        candidate_tokens = 0
        total_tokens = 0

        if isinstance(raw_resp, str):
            content_text = raw_resp
        else:
            content_text = getattr(raw_resp, "text", "") or ""
            finish_reason = getattr(raw_resp, "finish_reason", "STOP") or "STOP"

            usage_meta = getattr(raw_resp, "usage_metadata", None)
            if usage_meta:
                prompt_tokens = getattr(usage_meta, "prompt_token_count", 0) or 0
                candidate_tokens = getattr(usage_meta, "candidates_token_count", 0) or 0
                total_tokens = getattr(usage_meta, "total_token_count", 0) or (prompt_tokens + candidate_tokens)

        return LLMResponseDTO(
            content=content_text,
            model=self._model_name,
            finish_reason=str(finish_reason),
            prompt_tokens=prompt_tokens,
            candidate_tokens=candidate_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            correlation_id=correlation_id,
        )
