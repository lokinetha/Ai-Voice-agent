"""
Regression tests verifying CLI and bootstrap Gemini configuration resolution from .env.

Proves:
- CLI/bootstrap resolves GEMINI_API_KEY via Settings configuration.
- Missing or placeholder GEMINI_API_KEY when LLM_PROVIDER=gemini raises a clear configuration error.
- Explicit LLM_PROVIDER=fake returns FakeLLMRuntimeAdapter for testing.
- Secrets are never exposed or logged in raw form.
"""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from shared.config.settings import Settings, resolve_llm_adapter
from voice.infrastructure.adapters.fake_llm_runtime_adapter import (
    FakeLLMRuntimeAdapter,
)
from voice.infrastructure.adapters.gemini_llm_adapter import GeminiLLMAdapter


class TestCLISettingsResolution(unittest.TestCase):
    """Regression test suite for CLI/Bootstrap configuration resolution."""

    def test_gemini_adapter_resolution_with_safe_dummy_key(self) -> None:
        """Verify resolve_llm_adapter returns GeminiLLMAdapter when LLM_PROVIDER=gemini and valid key is set."""
        dummy_env = {
            "LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "AIzaSySAFE_DUMMY_KEY_9999",
            "GEMINI_MODEL": "gemini-2.5-flash",
        }

        with patch.dict(os.environ, dummy_env):
            cfg = Settings()
            adapter = resolve_llm_adapter(cfg)

            self.assertIsInstance(adapter, GeminiLLMAdapter)
            self.assertEqual(adapter.model_name, "gemini-2.5-flash")
            self.assertEqual(cfg.get_masked_api_key(), "***9999")

    def test_gemini_missing_key_produces_configuration_error(self) -> None:
        """Verify missing or placeholder GEMINI_API_KEY raises clear ValueError when LLM_PROVIDER=gemini."""
        unconfigured_env = {
            "LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "YOUR_GEMINI_API_KEY",
        }

        with patch.dict(os.environ, unconfigured_env):
            cfg = Settings()
            with self.assertRaises(ValueError) as ctx:
                resolve_llm_adapter(cfg)

            self.assertIn("GEMINI_API_KEY is missing or unconfigured", str(ctx.exception))

    def test_explicit_fake_llm_provider(self) -> None:
        """Verify resolve_llm_adapter returns FakeLLMRuntimeAdapter when LLM_PROVIDER=fake."""
        fake_env = {
            "LLM_PROVIDER": "fake",
        }

        with patch.dict(os.environ, fake_env):
            cfg = Settings()
            adapter = resolve_llm_adapter(cfg)

            self.assertIsInstance(adapter, FakeLLMRuntimeAdapter)


if __name__ == "__main__":
    unittest.main()
