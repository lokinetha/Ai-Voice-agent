"""
Unit tests for GeminiLLMAdapter.

Tests successful generation, streaming, timeout, provider error mapping, retry backoff,
and secret masking without requiring a real API key.
"""

from __future__ import annotations

import asyncio
import unittest

from voice.infrastructure.adapters.gemini_llm_adapter import (
    GeminiLLMAdapter,
    LLMProviderError,
    LLMTimeoutError,
)


class MockUsageMetadata:
    def __init__(self, prompt: int = 15, candidate: int = 25) -> None:
        self.prompt_token_count = prompt
        self.candidates_token_count = candidate
        self.total_token_count = prompt + candidate


class MockGeminiResponse:
    def __init__(
        self,
        text: str = "Hello from Gemini!",
        finish_reason: str = "STOP",
        usage_metadata: MockUsageMetadata | None = None,
    ) -> None:
        self.text = text
        self.finish_reason = finish_reason
        self.usage_metadata = usage_metadata or MockUsageMetadata()


class MockGeminiClient:
    """Fake/Mock Gemini Client for testing without external API calls."""

    def __init__(
        self,
        response_text: str = "Hello from Gemini!",
        fail_count: int = 0,
        fail_error: Exception | None = None,
        slow_delay: float = 0.0,
    ) -> None:
        self.response_text = response_text
        self.fail_count = fail_count
        self.fail_error = fail_error or RuntimeError("503 Service Unavailable")
        self.slow_delay = slow_delay
        self.calls = 0

    async def generate_content(
        self, contents: list[dict], model: str = "", system_instruction: str = ""
    ) -> MockGeminiResponse:
        self.calls += 1
        if self.slow_delay > 0.0:
            await asyncio.sleep(self.slow_delay)
        if self.calls <= self.fail_count:
            raise self.fail_error
        return MockGeminiResponse(text=self.response_text)

    def generate_content_stream(
        self, contents: list[dict], model: str = "", system_instruction: str = ""
    ) -> list[MockGeminiResponse]:
        self.calls += 1
        if self.calls <= self.fail_count:
            raise self.fail_error
        return [
            MockGeminiResponse(text="Hello "),
            MockGeminiResponse(text="from "),
            MockGeminiResponse(text="Gemini!"),
        ]


class TestGeminiLLMAdapter(unittest.TestCase):
    """Unit test suite for GeminiLLMAdapter."""

    def test_successful_generation(self) -> None:
        async def run() -> None:
            mock_client = MockGeminiClient(response_text="AI Agent response text")
            adapter = GeminiLLMAdapter(
                api_key="AIzaSyFAKE_KEY_12345",
                model_name="gemini-2.5-flash",
                client=mock_client,
            )

            res = await adapter.generate_response(
                workspace_id="ws-100",
                agent_id="ag-100",
                conversation_id="conv-100",
                prompt_text="What is your pricing?",
                compiled_prompt="You are a helpful sales AI agent.",
                knowledge_context=["Pricing starts at $10/mo."],
            )

            self.assertEqual(res.content, "AI Agent response text")
            self.assertEqual(res.model, "gemini-2.5-flash")
            self.assertEqual(res.finish_reason, "STOP")
            self.assertEqual(res.prompt_tokens, 15)
            self.assertEqual(res.candidate_tokens, 25)
            self.assertEqual(res.total_tokens, 40)
            self.assertEqual(res.correlation_id, "ws-100:conv-100")
            self.assertGreaterEqual(res.latency_ms, 0.0)

            # Test string representation backward compatibility
            self.assertEqual(str(res), "AI Agent response text")

        asyncio.run(run())

    def test_streaming_generation(self) -> None:
        async def run() -> None:
            mock_client = MockGeminiClient()
            adapter = GeminiLLMAdapter(client=mock_client)

            chunks: list[str] = []
            async for chunk in adapter.generate_response_stream(
                workspace_id="ws-100",
                agent_id="ag-100",
                conversation_id="conv-100",
                prompt_text="Hi",
            ):
                chunks.append(chunk)

            self.assertEqual("".join(chunks), "Hello from Gemini!")

        asyncio.run(run())

    def test_retry_on_transient_failure(self) -> None:
        async def run() -> None:
            # Fails first attempt with 503, succeeds on 2nd attempt
            mock_client = MockGeminiClient(
                response_text="Recovered response",
                fail_count=1,
                fail_error=RuntimeError("503 Service Unavailable"),
            )
            adapter = GeminiLLMAdapter(
                client=mock_client,
                max_retries=2,
                retry_delay_seconds=0.01,
            )

            res = await adapter.generate_response(
                workspace_id="ws-1",
                agent_id="ag-1",
                conversation_id="conv-1",
                prompt_text="Retry test",
            )

            self.assertEqual(res.content, "Recovered response")
            self.assertEqual(mock_client.calls, 2)

        asyncio.run(run())

    def test_timeout_handling(self) -> None:
        async def run() -> None:
            mock_client = MockGeminiClient(slow_delay=0.2)
            adapter = GeminiLLMAdapter(
                client=mock_client,
                timeout_seconds=0.05,
                max_retries=0,
            )

            with self.assertRaises(LLMTimeoutError):
                await adapter.generate_response(
                    workspace_id="ws-1",
                    agent_id="ag-1",
                    conversation_id="conv-1",
                    prompt_text="Timeout test",
                )

        asyncio.run(run())

    def test_secret_masking(self) -> None:
        async def run() -> None:
            fake_key = "AIzaSyTESTSECRETKEY999"
            mock_client = MockGeminiClient(
                fail_count=5,
                fail_error=RuntimeError(f"Authentication failed with key {fake_key}"),
            )
            adapter = GeminiLLMAdapter(
                api_key=fake_key,
                client=mock_client,
                max_retries=0,
            )

            try:
                await adapter.generate_response(
                    workspace_id="ws-1",
                    agent_id="ag-1",
                    conversation_id="conv-1",
                    prompt_text="Secret test",
                )
            except LLMProviderError as err:
                self.assertNotIn(fake_key, str(err))
                self.assertIn("***Y999", str(err))

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
